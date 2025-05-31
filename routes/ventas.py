from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import func
from db import sesion, Venta, DetalleVenta, Cliente, Producto, login_required, rol_requerido, Ubicacion, StockPorUbicacion
from decimal import Decimal
from routes.productos import productos_bp
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from routes.graficas_py import generar_grafico_ventas_por_ubicacion


ventas_bp = Blueprint("ventas", __name__)

@ventas_bp.route("/ventas")
@login_required

# 🧾 ventas()
# ES: Muestra un listado de ventas con filtros por cliente y estado de pago, paginación y orden.
# EN: Displays a list of sales with filters by client and payment status, including pagination and ordering.

def ventas():
    cliente = request.args.get("cliente")
    pagado = request.args.get("pagado")
    pagina = int(request.args.get("pagina", 1))
    orden = request.args.get("orden", "id")
    direccion = request.args.get("direccion", "desc")
    por_pagina = 30

    query = sesion.query(Venta).join(Cliente)

    if cliente:
        query = query.filter(Cliente.nombre.ilike(f"%{cliente}%"))
    if pagado in ["0", "1"]:
        query = query.filter(Venta.pagado == bool(int(pagado)))

    def aplicar_orden(campo):
        return campo.desc() if direccion == "desc" else campo.asc()

    if orden == "cliente":
        query = query.order_by(aplicar_orden(Cliente.nombre))
    elif orden == "fecha":
        query = query.order_by(aplicar_orden(Venta.fecha))
    else:
        query = query.order_by(aplicar_orden(Venta.id))

    total_ventas = query.count()
    ventas = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    hay_anterior = pagina > 1
    hay_siguiente = (pagina * por_pagina) < total_ventas

    return render_template("ventas/ventas.html",
        ventas=ventas,
        pagina=pagina,
        hay_anterior=hay_anterior,
        hay_siguiente=hay_siguiente,
        cliente=cliente,
        pagado=pagado,
        orden=orden,
        direccion=direccion
    )

@ventas_bp.route("/nueva_venta", methods=["GET", "POST"])
@rol_requerido('admin')

# 🆕 nueva_venta()
# ES: Permite registrar una nueva venta. Valida stock por ubicación y descuenta unidades tras la venta.
# EN: Allows registering a new sale. Validates stock by location and updates quantities after the sale.

def nueva_venta():
    clientes = sesion.query(Cliente).all()
    productos = sesion.query(Producto).all()
    ubicaciones = sesion.query(Ubicacion).all()

    # 🔧 Convertir los productos a JSON serializable
    productos_json = [
        {"id": p.id, "nombre": p.nombre, "precio": float(p.precio)}
        for p in productos
    ]
    datos_previos = {}  # ← así siempre existirá, incluso en GET

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        productos_ids = request.form.getlist("producto_id[]")
        cantidades = request.form.getlist("cantidad[]")
        descuento = float(request.form.get("descuento", 0.0))
        ubicacion_id = int(request.form.get("ubicacion_id"))

        total = 0
        detalles = []
        datos_previos = {
            "cliente_id": cliente_id,
            "productos_ids": productos_ids,
            "cantidades": cantidades,
            "descuento": descuento,
            "ubicacion_id": ubicacion_id
        }

        for i in range(len(productos_ids)):
            producto = sesion.query(Producto).get(productos_ids[i])
            cantidad = int(cantidades[i])

            stock_ubicado = sesion.query(StockPorUbicacion).filter_by(
                producto_id=producto.id,
                ubicacion_id=ubicacion_id
            ).first()

            if not stock_ubicado or stock_ubicado.cantidad < cantidad:
                disponible = stock_ubicado.cantidad if stock_ubicado else 0
                flash(f"No hay suficiente stock de {producto.nombre} en esta ubicación. Quedan {disponible}.", "error")
                return render_template("ventas/nueva_venta.html",
                                       clientes=clientes,
                                       productos=productos,
                                       ubicaciones=ubicaciones,
                                       datos_previos=datos_previos,
                                       productos_json=productos_json)  # ← ESTA LÍNEA FALTABA

            subtotal = cantidad * producto.precio
            total += subtotal

            detalles.append({
                "producto_id": producto.id,
                "cantidad": cantidad,
                "precio_unitario": producto.precio,
                "subtotal": subtotal
            })

        total_final = total * (1 - Decimal(descuento) / 100)
        nueva_venta = Venta(
            cliente_id=cliente_id,
            ubicacion_id=ubicacion_id,
            total=total,
            descuento=descuento,
            total_final=total_final
        )
        sesion.add(nueva_venta)
        sesion.flush()

        for detalle in detalles:
            sesion.add(DetalleVenta(venta_id=nueva_venta.id, **detalle))

            stock_ubicado = sesion.query(StockPorUbicacion).filter_by(
                producto_id=detalle["producto_id"],
                ubicacion_id=ubicacion_id
            ).first()

            if stock_ubicado:
                stock_ubicado.cantidad -= detalle["cantidad"]

        sesion.commit()

        # 🔁 Actualiza la gráfica después de registrar la venta
        generar_grafico_ventas_por_ubicacion

        flash("Venta registrada con éxito ✅", "success")
        return redirect(url_for("ventas.ventas"))

    return render_template("ventas/nueva_venta.html",
                           clientes=clientes,
                           productos=productos,
                           ubicaciones=ubicaciones,
                           datos_previos=datos_previos,
                           productos_json=productos_json)


#Cambia estado de pago
@ventas_bp.route("/cambiar_estado_pago/<int:venta_id>/<int:nuevo_estado>", methods=["POST"])
@login_required

# 🔁 cambiar_estado_pago()
# ES: Cambia el estado de pago (pagado/no pagado) de una venta concreta.
# EN: Changes the payment status (paid/unpaid) of a specific sale.

def cambiar_estado_pago(venta_id, nuevo_estado):
    # Usamos `sesion` en lugar de `db`
    venta = sesion.get(Venta, venta_id)  # Aquí cambiamos db por sesion
    if venta:
        # Convertir el estado numérico a booleano
        venta.pagado = bool(nuevo_estado)
        sesion.commit()  # Guardar los cambios en la base de datos
        return jsonify({"success": True})  # Respuesta exitosa

    return jsonify({"success": False}), 404  # Si la venta no se encuentra, devolver error 404


@ventas_bp.route("/venta_detalle/<int:venta_id>")
@login_required

# 🔎 ver_detalle_venta()
# ES: Muestra los detalles de una venta específica, incluyendo productos y precios.
# EN: Displays the details of a specific sale, including products and pricing.

def ver_detalle_venta(venta_id):
    # Obtener la venta y sus productos asociados
    venta = sesion.query(Venta).get(venta_id)
    if not venta:
        return "Venta no encontrada", 404

    # Obtener los detalles de la venta (productos vendidos en esa venta)
    detalles = sesion.query(DetalleVenta).filter(DetalleVenta.venta_id == venta.id).all()

    # Si hay detalles, obtener los productos
    productos = []
    for detalle in detalles:
        producto = sesion.query(Producto).get(detalle.producto_id)
        productos.append({
            "id": detalle.id,
            "nombre": producto.nombre,
            "cantidad": detalle.cantidad,
            "precio": detalle.precio_unitario  # Usamos el precio_unitario del detalle
        })

    # Renderizar una plantilla para mostrar los detalles de la venta
    return render_template("ventas/detalle_venta.html",
                           venta=venta,
                           productos=productos,
                           descuento=venta.descuento,
                           total_final=venta.total_final)




@ventas_bp.route("/registrar_venta", methods=["POST"])
@rol_requerido('admin')

# 🧾 registrar_venta()
# ES: Registra una venta directa desde formulario, valida stock y descuenta productos.
# EN: Registers a sale from a form, validates stock, and updates product quantities.

def registrar_venta():
    # Datos recibidos del formulario de venta
    productos_vendidos = request.form.getlist('productos')  # Lista de productos vendidos
    cantidades_vendidas = request.form.getlist('cantidades')  # Cantidades vendidas
    cliente_id = request.form.get('cliente_id')  # ID del cliente
    total = request.form.get('total')  # Total de la venta
    descuento = request.form.get('descuento')  # Descuento aplicado
    total_final = total - descuento  # Total después del descuento

    # Crear la venta
    venta = Venta(cliente_id=cliente_id, total=total, descuento=descuento, total_final=total_final)
    db.session.add(venta)

    # Iterar sobre los productos vendidos
    for producto_id, cantidad in zip(productos_vendidos, cantidades_vendidas):
        producto = db.session.query(Producto).get(producto_id)

        # Verificar si hay suficiente stock
        if producto.stock < int(cantidad):
            flash(f"No hay suficiente stock de {producto.nombre}. Solo quedan {producto.stock} unidades.", "error")
            return redirect(url_for('ventas.ventas'))  # Redirigir al listado de ventas

        # Crear el detalle de la venta
        detalle = DetalleVenta(venta_id=venta.id, producto_id=producto.id, cantidad=int(cantidad),
                               precio_unitario=producto.precio, subtotal=producto.precio * int(cantidad))
        db.session.add(detalle)

        # Descontar el stock del producto
        producto.stock -= int(cantidad)

    # Guardar cambios en la base de datos
    db.session.commit()

    flash("Venta registrada exitosamente.", "success")
    return redirect(url_for('ventas.ventas'))  # Redirigir al listado de ventas


#Gráficas
@ventas_bp.route('/graficas_ventas')
@login_required

# 📊 graficas_ventas()
# ES: Muestra la plantilla base para ver gráficas relacionadas con ventas.
# EN: Displays the base template for viewing sales-related graphs.

def graficas_ventas():
    return render_template('ventas/graficas.html')


#Venta por productos
@ventas_bp.route("/datos_ventas")
@login_required

# 📈 datos_ventas()
# ES: Devuelve datos agregados por producto en formato JSON para usar en gráficas.
# EN: Returns aggregated product data in JSON format for use in graphs.

def datos_ventas():
    # Realizar la consulta para obtener la suma de las cantidades por producto
    datos = sesion.query(
        Producto.nombre.label("producto_nombre"),  # Alias para evitar ambigüedad
        func.sum(DetalleVenta.cantidad).label("total_cantidad")
    ) \
    .join(DetalleVenta, Producto.id == DetalleVenta.producto_id) \
    .group_by(Producto.nombre) \
    .all()

    # Preparar los datos para la respuesta JSON
    productos = [producto for producto, cantidad in datos]
    cantidades = [cantidad for producto, cantidad in datos]

    # Devolver los datos como JSON
    return jsonify({"productos": productos, "cantidades": cantidades})




@ventas_bp.route('/ventas/eliminar/<int:venta_id>', methods=['POST'])
@login_required
@rol_requerido('admin')

# ❌ eliminar_venta()
# ES: Elimina una venta y sus detalles asociados de la base de datos.
# EN: Deletes a sale and its associated details from the database.

def eliminar_venta(venta_id):
    venta = sesion.query(Venta).get(venta_id)
    if not venta:
        flash("Venta no encontrada", "error")
        return redirect(url_for("ventas.ventas"))

    # Eliminar los detalles asociados primero si existe relación
    for detalle in venta.detalles:
        sesion.delete(detalle)

    sesion.delete(venta)
    sesion.commit()
    flash("Venta eliminada correctamente 🧨", "success")
    return redirect(url_for("ventas.ventas"))


@ventas_bp.route('/ventas/eliminar_producto/<int:detalle_id>', methods=['POST'])
@login_required
@rol_requerido('admin')

# 🗑️ eliminar_producto()
# ES: Elimina un producto específico de una venta y actualiza la base de datos.
# EN: Deletes a specific product from a sale and updates the database.

def eliminar_producto(detalle_id):
    detalle = sesion.query(DetalleVenta).get(detalle_id)
    if not detalle:
        flash("Producto no encontrado en la venta", "error")
        return redirect(url_for("ventas.ventas"))

    venta_id = detalle.venta_id  # para redirigir de vuelta a la factura
    sesion.delete(detalle)
    sesion.commit()
    flash("Producto eliminado de la venta 🗑️", "success")
    return redirect(url_for("ventas.ver_detalle_venta", venta_id=venta_id))


@ventas_bp.route('/ventas/editar_producto/<int:detalle_id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin')

# ✏️ editar_producto()
# ES: Permite modificar la cantidad o precio unitario de un producto en una venta.
# EN: Allows modifying the quantity or unit price of a product in a sale.

def editar_producto(detalle_id):
    detalle = sesion.query(DetalleVenta).get(detalle_id)
    if not detalle:
        flash("Detalle de venta no encontrado.", "error")
        return redirect(url_for("ventas.ventas"))

    producto = sesion.query(Producto).get(detalle.producto_id)

    if request.method == 'POST':
        nueva_cantidad = int(request.form['cantidad'])
        nuevo_precio = float(request.form['precio_unitario'])
        detalle.cantidad = nueva_cantidad
        detalle.precio_unitario = nuevo_precio
        detalle.subtotal = nueva_cantidad * nuevo_precio
        sesion.commit()
        flash("Producto de la venta actualizado correctamente ✅", "success")
        return redirect(url_for('ventas.ver_detalle_venta', venta_id=detalle.venta_id))

    return render_template("ventas/editar_producto_venta.html", detalle=detalle, producto=producto)




#Facturas pdf


@ventas_bp.route('/ventas/factura/<int:id>')
@login_required

# 📄 descargar_factura()
# ES: Genera una factura en PDF con los datos de la venta, cliente y productos.
# EN: Generates a PDF invoice with sale, client, and product data.

def descargar_factura(id):
    venta = sesion.query(Venta).get(id)
    detalles = venta.detalles

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elementos = []

    estilos = getSampleStyleSheet()

    # 🧾 Datos de empresa
    empresa = [
        "JCM INFORMÁTICA",
        "Sevilla, 41008",
        "Tel: 635487063",
        "Email: jcm201080@gmail.com"
    ]
    for linea in empresa:
        elementos.append(Paragraph(linea, estilos["Normal"]))
    elementos.append(Spacer(1, 12))

    # 🧾 Datos de la factura
    elementos.append(Paragraph(f"<strong>Factura N°:</strong> {venta.id}", estilos["Normal"]))
    elementos.append(Paragraph(f"<strong>Cliente:</strong> {venta.cliente.nombre}", estilos["Normal"]))
    elementos.append(Paragraph(f"<strong>Fecha:</strong> {venta.fecha.strftime('%d/%m/%Y')}", estilos["Normal"]))
    elementos.append(Spacer(1, 12))

    # 🧾 Tabla de productos
    data = [["Producto", "Cantidad", "Precio unitario (€)", "Subtotal (€)"]]
    for detalle in detalles:
        fila = [
            detalle.producto.nombre,
            detalle.cantidad,
            f"{detalle.precio_unitario:.2f}",
            f"{detalle.subtotal:.2f}"
        ]
        data.append(fila)

    # Total final
    data.append(["", "", "Total:", f"{venta.total_final:.2f}"])

    tabla = Table(data, colWidths=[150, 80, 100, 100])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
    ]))

    elementos.append(tabla)
    doc.build(elementos)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name=f"factura_{venta.id}.pdf", mimetype='application/pdf')