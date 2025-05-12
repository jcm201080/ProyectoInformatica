from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor, login_required, rol_requerido, Compra

from routes.clientes import clientes
from routes.productos import nuevo_producto
from sqlalchemy import desc

compras_bp = Blueprint('compras', __name__)

@compras_bp.route('/compras')
@login_required
def compras():
    compras = sesion.query(Compra).order_by(desc(Compra.id)).all()
    return render_template('compras/compras.html', compras=compras)


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


