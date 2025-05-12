from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.dialects.mysql import DECIMAL
from sqlalchemy import func
from db import sesion, Venta, DetalleVenta, Cliente, Producto, login_required, rol_requerido
from decimal import Decimal
from routes.productos import productos_bp

ventas_bp = Blueprint("ventas", __name__)

@ventas_bp.route("/ventas")
@login_required
def ventas():
    # Obtener los parámetros de búsqueda (si existen)
    cliente = request.args.get("cliente")
    pagado = request.args.get("pagado")

    # Empezar con la consulta base
    query = sesion.query(Venta)  # Usamos sesion.query en lugar de Venta.query

    # Si se pasa un nombre de cliente, filtramos las ventas que corresponden a ese cliente
    if cliente:
        query = query.join(Cliente).filter(Cliente.nombre.ilike(f"%{cliente}%"))

    # Si se pasa un estado de pago, filtramos las ventas según el estado (0 o 1)
    if pagado in ["0", "1"]:
        query = query.filter(Venta.pagado == bool(int(pagado)))

    # Ejecutamos la consulta
    ventas = query.order_by(Venta.id.desc()).all()   # Ordena por ID de mayor a menor

    # Renderizamos la plantilla con las ventas obtenidas
    return render_template("ventas/ventas.html", ventas=ventas)





@ventas_bp.route("/nueva_venta", methods=["GET", "POST"])
@rol_requerido('admin')
def nueva_venta():
    clientes = sesion.query(Cliente).all()
    productos = sesion.query(Producto).all()

    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        productos_ids = request.form.getlist("producto_id[]")
        cantidades = request.form.getlist("cantidad[]")
        descuento = float(request.form.get("descuento", 0.0))

        total = 0
        detalles = []

        # Validar si el stock es suficiente antes de proceder
        for i in range(len(productos_ids)):
            producto = sesion.query(Producto).get(productos_ids[i])
            cantidad = int(cantidades[i])

            # Verificar si hay suficiente stock
            if producto.stock < cantidad:
                flash(f"No hay suficiente stock de {producto.nombre}. Solo quedan {producto.stock} unidades.", "error")
                return redirect(url_for("ventas.nueva_venta"))  # Redirigir al formulario de venta

            precio_unitario = producto.precio
            subtotal = cantidad * precio_unitario
            total += subtotal

            detalles.append({
                "producto_id": producto.id,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal
            })

            # Restar del stock
            print(f"Restando {cantidad} unidades de {producto.nombre} (stock antes: {producto.stock})")
            producto.stock -= cantidad
            print(f"Nuevo stock de {producto.nombre}: {producto.stock}")  # Verificar el stock actualizado

        total_final = total * (1 - Decimal(descuento) / 100)

        # Crear la venta
        nueva_venta = Venta(cliente_id=cliente_id, total=total, descuento=descuento, total_final=total_final)
        sesion.add(nueva_venta)
        sesion.commit()

        # Agregar detalles de la venta
        for detalle in detalles:
            det = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=detalle["producto_id"],
                cantidad=detalle["cantidad"],
                precio_unitario=detalle["precio_unitario"],
                subtotal=detalle["subtotal"]
            )
            sesion.add(det)

        sesion.commit()  # Guardar todo (incluyendo los cambios en el stock)
        flash("Venta registrada con éxito", "success")
        return redirect(url_for("ventas.ventas"))

    return render_template("ventas/nueva_venta.html", clientes=clientes, productos=productos)


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
