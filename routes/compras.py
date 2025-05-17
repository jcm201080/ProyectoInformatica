from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor, login_required, rol_requerido, Compra

from routes.clientes import clientes
from routes.productos import nuevo_producto
from sqlalchemy import desc
from datetime import datetime

compras_bp = Blueprint('compras', __name__)

@compras_bp.route('/compras')
@login_required
def compras():
    proveedor = request.args.get("proveedor")
    pagina = int(request.args.get("pagina", 1))
    orden = request.args.get("orden", "id")
    direccion = request.args.get("direccion", "desc")
    por_pagina = 30

    query = sesion.query(Compra).join(Proveedor)

    if proveedor:
        query = query.filter(Proveedor.nombre.ilike(f"%{proveedor}%"))

    def aplicar_orden(campo):
        return campo.desc() if direccion == "desc" else campo.asc()

    if orden == "proveedor":
        query = query.order_by(aplicar_orden(Proveedor.nombre))
    elif orden == "fecha":
        query = query.order_by(aplicar_orden(Compra.fecha))
    else:
        query = query.order_by(aplicar_orden(Compra.id))

    total_compras = query.count()
    compras = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    hay_anterior = pagina > 1
    hay_siguiente = (pagina * por_pagina) < total_compras

    return render_template("compras/compras.html",
        compras=compras,
        pagina=pagina,
        hay_anterior=hay_anterior,
        hay_siguiente=hay_siguiente,
        proveedor=proveedor,
        orden=orden,
        direccion=direccion
    )



@compras_bp.route('/nueva_compra', methods=['GET', 'POST'])
def nueva_compra():
    productos = sesion.query(Producto).all()
    proveedores = sesion.query(Proveedor).all()

    if request.method == "POST":
        producto_id = request.form["producto_id"]
        proveedor_id = request.form["proveedor_id"]
        precio = float(request.form["precio"])
        cantidad = int(request.form["cantidad"])

        # Obtener el producto
        producto = sesion.query(Producto).get(producto_id)
        if not producto:
            flash("Producto no encontrado", "error")
            return redirect(url_for("compras.nueva_compra"))

        # Validar si supera la capacidad máxima (cantidad)
        nuevo_stock = producto.stock + cantidad
        if nuevo_stock > producto.cantidad_total:  # Si excede la capacidad máxima
            flash(
                f"¡Alerta! Capacidad máxima superada: {nuevo_stock}/{producto.cantidad_total} unidades. "
                f"Has añadido {nuevo_stock-producto.cantidad_total} unidades de más.",
                "warning"
            )
        else:
            flash("Compra dentro del límite de capacidad.", "info")

        # Actualizar stock (aunque haya excedido el límite)
        producto.stock = nuevo_stock

        # Registrar la compra
        nueva_compra = Compra(
            producto_id=producto_id,
            proveedor_id=proveedor_id,
            precio=precio,
            cantidad=cantidad,
            total=precio * cantidad
        )
        sesion.add(nueva_compra)
        sesion.commit()

        flash(f"Compra registrada. Stock actual: {producto.stock}/{producto.cantidad_total}", "success")
        return redirect(url_for("compras.compras"))

    return render_template("compras/nueva_compra.html", productos=productos, proveedores=proveedores)


@compras_bp.route('/compras/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin')
def editar_compra(id):
    compra = sesion.query(Compra).get(id)
    proveedores = sesion.query(Proveedor).all()

    if request.method == 'POST':
        compra.fecha = request.form['fecha']
        compra.proveedor_id = request.form['proveedor_id']
        compra.total = float(request.form['total'])
        compra.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()

        sesion.commit()
        flash('Compra actualizada correctamente ✅', 'success')
        return redirect(url_for('compras.compras'))

    return render_template('compras/editar_compra.html', compra=compra, proveedores=proveedores)


@compras_bp.route('/compras/eliminar/<int:id>', methods=['POST'])
@login_required
@rol_requerido('admin')
def eliminar_compra(id):
    compra = sesion.query(Compra).get(id)
    if not compra:
        flash('Compra no encontrada.', 'error')
        return redirect(url_for('compras.compras'))

    sesion.delete(compra)
    sesion.commit()
    flash('Compra eliminada correctamente 🗑️', 'success')
    return redirect(url_for('compras.compras'))
