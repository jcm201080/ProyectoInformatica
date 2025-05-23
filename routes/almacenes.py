# rutas/almacenes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Ubicacion, StockPorUbicacion, login_required

almacenes_bp = Blueprint('almacenes', __name__)

@almacenes_bp.route('/almacenes')
@login_required
def ver_almacenes():
    nombre = request.args.get("nombre", "")
    pagina = int(request.args.get("pagina", 1))
    orden = request.args.get("orden", "producto")
    direccion = request.args.get("direccion", "asc")
    por_pagina = 30

    ubicaciones = sesion.query(Ubicacion).all()

    # Filtro por nombre si se proporciona
    query = sesion.query(Producto)
    if nombre:
        query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))

    # Aplicar orden
    if orden == "producto":
        if direccion == "desc":
            query = query.order_by(Producto.nombre.desc())
        else:
            query = query.order_by(Producto.nombre.asc())

    total = query.count()
    productos = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    datos_stock = []
    for producto in productos:
        stock_por_ubicacion = {u.nombre: 0 for u in ubicaciones}
        for entrada in producto.ubicaciones_stock:
            stock_por_ubicacion[entrada.ubicacion.nombre] = entrada.cantidad

        datos_stock.append({
            "id": producto.id,
            "producto": producto.nombre,
            "stock": stock_por_ubicacion
        })

    hay_anterior = pagina > 1
    hay_siguiente = (pagina * por_pagina) < total

    return render_template("almacenes/almacenes.html",
                           datos_stock=datos_stock,
                           ubicaciones=ubicaciones,
                           nombre=nombre,
                           pagina=pagina,
                           orden=orden,
                           direccion=direccion,
                           hay_anterior=hay_anterior,
                           hay_siguiente=hay_siguiente)




#Mover productos entre ubicaciones (nueva ruta y formulario)
@almacenes_bp.route('/mover_producto', methods=['GET', 'POST'])
@login_required
def mover_producto():
    producto_id = request.args.get("producto_id")
    ubicaciones = sesion.query(Ubicacion).all()
    producto = sesion.query(Producto).get(producto_id) if producto_id else None

    # Stock actual en Almacén o ubicación central
    stock_actual = 0
    if producto:
        ubicacion_origen = sesion.query(Ubicacion).filter_by(nombre="Almacén").first()
        stock = sesion.query(StockPorUbicacion).filter_by(producto_id=producto.id, ubicacion_id=ubicacion_origen.id).first()
        stock_actual = stock.cantidad if stock else 0

    if request.method == 'POST':
        destino_id = int(request.form['destino_id'])
        cantidad = int(request.form['cantidad'])

        ubicacion_origen = sesion.query(Ubicacion).filter_by(nombre="Almacén").first()
        stock_origen = sesion.query(StockPorUbicacion).filter_by(producto_id=producto.id, ubicacion_id=ubicacion_origen.id).first()

        if not stock_origen or stock_origen.cantidad < cantidad:
            flash("No hay suficiente stock disponible para mover.", "error")
            return redirect(url_for("almacenes.mover_producto", producto_id=producto.id))

        stock_destino = sesion.query(StockPorUbicacion).filter_by(producto_id=producto.id, ubicacion_id=destino_id).first()

        if not stock_destino:
            stock_destino = StockPorUbicacion(
                producto_id=producto.id,
                ubicacion_id=destino_id,
                cantidad=0
            )
            sesion.add(stock_destino)

        stock_origen.cantidad -= cantidad
        stock_destino.cantidad += cantidad
        sesion.commit()

        flash("✅ Producto movido correctamente.", "success")
        return redirect(url_for("almacenes.ver_almacenes"))

    return render_template("almacenes/mover_producto.html", producto=producto, ubicaciones=ubicaciones, stock_actual=stock_actual)
