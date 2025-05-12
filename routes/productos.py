from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor, login_required, rol_requerido

from routes.clientes import clientes

productos_bp = Blueprint('productos', __name__)

#Nota ver_producto es la principal, y productos la de añadir los productos, debo cambiarla

#Acceso a todos los usuarios que estan registrados
@productos_bp.route('/productos')
@login_required
def ver_productos():
    orden = request.args.get("orden", "id")
    direccion = request.args.get("direccion", "asc")

    query = sesion.query(Producto)

    # Función auxiliar para aplicar dirección
    def aplicar_direccion(campo):
        return campo.desc() if direccion == "desc" else campo.asc()

    if orden == "nombre":
        query = query.order_by(aplicar_direccion(Producto.nombre))
    elif orden == "precio":
        query = query.order_by(aplicar_direccion(Producto.precio))
    elif orden == "proveedor":
        from db import Proveedor
        query = query.join(Producto.proveedor).order_by(aplicar_direccion(Proveedor.nombre))
    else:
        query = query.order_by(aplicar_direccion(Producto.id))

    productos = query.all()
    return render_template("producto/productos.html", productos=productos, orden=orden, direccion=direccion)



#Solo pueden añadir nuevos productos los adminitradores
@productos_bp.route('/nuevo_producto')
@rol_requerido('admin')
def nuevo_producto():
    proveedores = sesion.query(Proveedor).all()
    return render_template('producto/nuevo_producto.html', proveedores=proveedores)

@productos_bp.route('/add_product', methods=['POST'])
@rol_requerido('admin')
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

    return redirect(url_for('productos.nuevo_producto'))



@productos_bp.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@rol_requerido('admin')
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
        producto.cantidad_total = int(request.form['cantidad_total'])

        sesion.commit()
        flash('Producto actualizado correctamente.')
        return redirect(url_for('productos.ver_productos'))

    return render_template('producto/editar_producto.html', producto=producto)

@productos_bp.route('/eliminar_producto/<int:id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_producto(id):
    producto = sesion.query(Producto).filter_by(id=id).first()

    if producto:
        sesion.delete(producto)
        sesion.commit()
        flash('Producto eliminado correctamente.')
    else:
        flash('Producto no encontrado.')

    return redirect(url_for('producto/productos.ver_productos'))


def verificar_stock_bajo():
    productos = sesion.query(Producto).all()

    for producto in productos:
        if producto.cantidad_total > 0:
            porcentaje = (producto.stock / producto.cantidad_total) * 100

            if porcentaje < 10:
                flash(f'¡Atención! El producto "{producto.nombre}" tiene menos del 10% de stock.', 'warning')









