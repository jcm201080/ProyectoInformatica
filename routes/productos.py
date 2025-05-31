from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, login_required, rol_requerido

# 🔹 Definir blueprint para productos / Define blueprint for products
productos_bp = Blueprint('productos', __name__)

# 📦 Vista principal de productos para usuarios registrados / Main product view for logged-in users
@productos_bp.route('/productos')
@login_required
def ver_productos():
    verificar_stock_bajo()

    orden = request.args.get("orden", "id")
    direccion = request.args.get("direccion", "asc")
    nombre = request.args.get("nombre", "")
    pagina = int(request.args.get("pagina", 1))
    por_pagina = 30

    query = sesion.query(Producto)

    if nombre:
        query = query.filter(
            (Producto.nombre.ilike(f"%{nombre}%")) |
            (Producto.descripcion.ilike(f"%{nombre}%"))
        )

    def aplicar_direccion(campo):
        return campo.desc() if direccion == "desc" else campo.asc()

    if orden == "nombre":
        query = query.order_by(aplicar_direccion(Producto.nombre))
    elif orden == "precio":
        query = query.order_by(aplicar_direccion(Producto.precio))
    else:
        query = query.order_by(aplicar_direccion(Producto.id))

    total_productos = query.count()
    productos = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

    hay_anterior = pagina > 1
    hay_siguiente = (pagina * por_pagina) < total_productos

    return render_template(
        "producto/productos.html",
        productos=productos,
        orden=orden,
        direccion=direccion,
        nombre=nombre,
        pagina=pagina,
        hay_anterior=hay_anterior,
        hay_siguiente=hay_siguiente
    )

# 🆕 Formulario para crear un nuevo producto (solo administradores) / Form to create a new product (admin only)
@productos_bp.route('/nuevo_producto')
@rol_requerido('admin')
def nuevo_producto():
    return render_template('producto/nuevo_producto.html')

# 💾 Procesamiento del formulario de nuevo producto / Handle new product form submission
@productos_bp.route('/add_product', methods=['POST'])
@rol_requerido('admin')
def add_product():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = request.form['precio']
    stock = request.form['stock']

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock
    )

    try:
        sesion.add(nuevo_producto)
        sesion.commit()
        flash("Producto añadido correctamente.")
    except Exception as e:
        sesion.rollback()
        flash(f"Error al añadir producto: {str(e)}")

    return redirect(url_for('productos.nuevo_producto'))

# ✏️ Edición de producto (solo administradores) / Edit product (admin only)
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
        producto.cantidad_total = int(request.form['cantidad_total'])

        try:
            sesion.commit()
            flash('Producto actualizado correctamente.')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al actualizar producto: {str(e)}')

        return redirect(url_for('productos.ver_productos'))

    return render_template('producto/editar_producto.html', producto=producto)

# ❌ Eliminar producto (solo administradores) / Delete product (admin only)
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

# ⚠️ Verificación de stock bajo (menos del 10%) / Low stock warning (<10%)
def verificar_stock_bajo():
    productos = sesion.query(Producto).all()

    for producto in productos:
        if producto.cantidad_total > 0:
            porcentaje = (producto.stock / producto.cantidad_total) * 100

            if porcentaje < 10:
                flash(f'¡Atención! El producto "{producto.nombre}" tiene menos del 10% de stock.', 'warning')
