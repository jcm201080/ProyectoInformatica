from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor

productos_bp = Blueprint('productos', __name__)

@productos_bp.route('/productos')
def productos():
    proveedores = sesion.query(Proveedor).all()
    return render_template('producto/producto.html', proveedores=proveedores)

@productos_bp.route('/add_product', methods=['POST'])
def add_product():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    stock = request.form['stock']
    proveedor_id = request.form['proveedor_id']

    if proveedor_id == "nuevo":
        return redirect(url_for('proveedores.proveedores'))  # Redirige para crear un proveedor

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        proveedor_id=int(proveedor_id)
    )

    try:
        sesion.add(nuevo_producto)
        sesion.commit()
        flash("Producto añadido correctamente.")
    except Exception as e:
        sesion.rollback()
        flash(f"Error al añadir producto: {str(e)}")

    return redirect(url_for('productos.productos'))

@productos_bp.route('/ver_productos')
def ver_productos():
    productos = sesion.query(Producto).all()
    return render_template('producto/ver_productos.html', productos=productos)

@productos_bp.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    producto = sesion.query(Producto).filter_by(id=id).first()

    if not producto:
        flash('Producto no encontrado.')
        return redirect(url_for('productos.ver_productos'))

    if request.method == 'POST':
        producto.nombre = request.form['nombre']
        producto.descripcion = request.form['descripcion']
        producto.precio = float(request.form['precio'])
        producto.stock = int(request.form['stock'])
        producto.proveedor_id = int(request.form['proveedor_id'])

        sesion.commit()
        flash('Producto actualizado correctamente.')
        return redirect(url_for('productos.ver_productos'))

    return render_template('producto/editar_producto.html', producto=producto)

@productos_bp.route('/eliminar_producto/<int:id>', methods=['POST'])
def eliminar_producto(id):
    producto = sesion.query(Producto).filter_by(id=id).first()

    if producto:
        sesion.delete(producto)
        sesion.commit()
        flash('Producto eliminado correctamente.')
    else:
        flash('Producto no encontrado.')

    return redirect(url_for('producto/productos.ver_productos'))
