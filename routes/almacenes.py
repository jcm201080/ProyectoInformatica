# routes/almacenes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import Session, Producto, Ubicacion, StockPorUbicacion, login_required

almacenes_bp = Blueprint('almacenes', __name__)

@almacenes_bp.route('/almacenes')
@login_required
def ver_almacenes():
    sesion = Session()
    try:
        nombre = request.args.get("nombre", "")
        pagina = int(request.args.get("pagina", 1))
        orden = request.args.get("orden", "producto")
        direccion = request.args.get("direccion", "asc")
        por_pagina = 30

        ubicaciones = sesion.query(Ubicacion).all()

        query = sesion.query(Producto)
        if nombre:
            query = query.filter(Producto.nombre.ilike(f"%{nombre}%"))

        if orden == "producto":
            query = query.order_by(
                Producto.nombre.desc() if direccion == "desc" else Producto.nombre.asc()
            )

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

        return render_template(
            "almacenes/almacenes.html",
            datos_stock=datos_stock,
            ubicaciones=ubicaciones,
            nombre=nombre,
            pagina=pagina,
            orden=orden,
            direccion=direccion,
            hay_anterior=hay_anterior,
            hay_siguiente=hay_siguiente
        )
    finally:
        sesion.close()


@almacenes_bp.route('/mover_producto', methods=['GET', 'POST'])
@login_required
def mover_producto():
    sesion = Session()
    try:
        producto_id = request.args.get("producto_id")
        ubicaciones = sesion.query(Ubicacion).all()
        producto = sesion.get(Producto, producto_id) if producto_id else None

        if request.method == 'POST':
            origen_id = int(request.form['origen_id'])
            destino_id = int(request.form['destino_id'])
            cantidad = int(request.form['cantidad'])

            if origen_id == destino_id:
                flash("La ubicación origen y destino no pueden ser iguales.", "error")
                return redirect(url_for("almacenes.mover_producto", producto_id=producto_id))

            stock_origen = sesion.query(StockPorUbicacion).filter_by(
                producto_id=producto.id, ubicacion_id=origen_id
            ).first()

            if not stock_origen or stock_origen.cantidad < cantidad:
                flash("No hay suficiente stock disponible en la ubicación origen.", "error")
                return redirect(url_for("almacenes.mover_producto", producto_id=producto_id))

            stock_destino = sesion.query(StockPorUbicacion).filter_by(
                producto_id=producto.id, ubicacion_id=destino_id
            ).first()

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
            return redirect(url_for("almacenes.mover_producto", producto_id=producto_id))

        return render_template(
            "almacenes/mover_producto.html",
            producto=producto,
            ubicaciones=ubicaciones
        )
    finally:
        sesion.close()
