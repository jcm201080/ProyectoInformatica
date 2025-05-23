from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import func
from db import sesion, Venta, DetalleVenta, Cliente, Producto, login_required, rol_requerido, Ubicacion, StockPorUbicacion
from decimal import Decimal
from routes.productos import productos_bp
from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet


ventas_bp = Blueprint("ventas", __name__)

@ventas_bp.route("/ventas")
@login_required
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
def nueva_venta():
    clientes = sesion.query(Cliente).all()
    productos = sesion.query(Producto).all()
    ubicaciones = sesion.query(Ubicacion).all()

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        productos_ids = request.form.getlist("producto_id[]")
        ubicacion_id = int(request.form["ubicacion_id"])  # ✅ convertir a int
        cantidades = request.form.getlist("cantidad[]")
        descuento = float(request.form.get("descuento", 0.0))
        total = 0
        detalles = []

        # Validar stock por ubicación
        for i in range(len(productos_ids)):
            producto = sesion.query(Producto).get(productos_ids[i])
            cantidad = int(cantidades[i])

            # Verificar si hay suficiente stock en esa ubicación
            stock_ubicacion = sesion.query(StockPorUbicacion).filter_by(
                producto_id=producto.id,
                ubicacion_id=ubicacion_id
            ).first()

            if not stock_ubicacion or stock_ubicacion.cantidad < cantidad:
                flash(f"No hay suficiente stock de {producto.nombre} en esta ubicación. Solo quedan {stock_ubicacion.cantidad if stock_ubicacion else 0} unidades.", "error")
                return redirect(url_for("ventas.nueva_venta"))

            # Restar del stock de la ubicación
            stock_ubicacion.cantidad -= cantidad

            # Opcional: actualizar también el stock total
            producto.stock -= cantidad

            precio_unitario = producto.precio
            subtotal = cantidad * precio_unitario
            total += subtotal

            detalles.append({
                "producto_id": producto.id,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })

        total_final = total * (1 - Decimal(descuento) / 100)

        # Crear la venta
        nueva_venta = Venta(
            cliente_id=cliente_id,
            ubicacion_id=ubicacion_id,
            total=total,
            descuento=descuento,
            total_final=total_final
        )
        sesion.add(nueva_venta)
        sesion.commit()

        # Añadir detalles de venta
        for detalle in detalles:
            det = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=detalle["producto_id"],
                cantidad=detalle["cantidad"],
                precio_unitario=detalle["precio_unitario"],
                subtotal=detalle["subtotal"]
            )
            sesion.add(det)

        sesion.commit()
        flash("Venta registrada con éxito", "success")
        return redirect(url_for("ventas.ventas"))

    return render_template("ventas/nueva_venta.html", clientes=clientes, productos=productos, ubicaciones=ubicaciones)



#Cambia estado de pago
@ventas_bp.route("/cambiar_estado_pago/<int:venta_id>/<int:nuevo_estado>", methods=["POST"])
@login_required
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
def graficas_ventas():
    return render_template('ventas/graficas.html')


#Venta por productos
@ventas_bp.route("/datos_ventas")
@login_required
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


#Venta por mes
@ventas_bp.route("/ventas_por_mes", methods=["GET"])
@login_required
def ventas_por_mes():
    mes = request.args.get("mes")

    if not mes:
        return jsonify({"error": "Debes proporcionar un mes en formato MM"}), 400

    try:
        datos = sesion.query(
            Producto.nombre.label("producto_nombre"),
            func.sum(DetalleVenta.cantidad).label("total_cantidad")
        ) \
        .join(DetalleVenta, Producto.id == DetalleVenta.producto_id) \
        .join(Venta, DetalleVenta.venta_id == Venta.id) \
        .filter(func.substr(Venta.fecha, 6, 2) == mes) \
        .group_by(Producto.nombre) \
        .all()

        productos = [producto for producto, cantidad in datos]
        cantidades = [cantidad for producto, cantidad in datos]

        return jsonify({"productos": productos, "cantidades": cantidades})

    except Exception as e:
        print("Error en ventas_por_mes:", e)
        return jsonify({"error": str(e)}), 500


@ventas_bp.route('/ventas/eliminar/<int:venta_id>', methods=['POST'])
@login_required
@rol_requerido('admin')
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
