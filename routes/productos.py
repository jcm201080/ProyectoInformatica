from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from db import Session, Producto, DetalleVenta, login_required, rol_requerido

productos_bp = Blueprint('productos', __name__)

# ⚠️ Verificación de stock bajo (menos del 10%)
def verificar_stock_bajo(sesion):
    productos = sesion.query(Producto).all()

    for producto in productos:
        if producto.cantidad_total > 0:
            porcentaje = (producto.stock / producto.cantidad_total) * 100
            if porcentaje < 10:
                flash(
                    f'¡Atención! El producto "{producto.nombre}" tiene menos del 10% de stock.',
                    'warning'
                )


# 📦 Vista principal de productos
@productos_bp.route('/productos')
@login_required
def ver_productos():
    sesion = Session()
    try:
        verificar_stock_bajo(sesion)

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
    finally:
        sesion.close()


# 🆕 Nuevo producto
@productos_bp.route('/nuevo_producto')
@rol_requerido('admin')
def nuevo_producto():
    return render_template('producto/nuevo_producto.html')


# 💾 Guardar nuevo producto
@productos_bp.route('/add_product', methods=['POST'])
@rol_requerido('admin')
def add_product():
    sesion = Session()
    try:
        nuevo_producto = Producto(
            nombre=request.form['nombre'],
            descripcion=request.form['descripcion'],
            precio=request.form['precio'],
            stock=request.form['stock']
        )

        sesion.add(nuevo_producto)
        sesion.commit()
        flash("Producto añadido correctamente.", "success")
    except IntegrityError:
        sesion.rollback()
        flash(
            f"Ya existe un producto con el nombre '{nuevo_producto.nombre}'.",
            "error"
        )
    except Exception as e:
        sesion.rollback()
        flash(f"Error al añadir producto: {str(e)}", "error")
    finally:
        sesion.close()

    return redirect(url_for('productos.nuevo_producto'))


# ✏️ Editar producto
@productos_bp.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
@rol_requerido('admin')
def editar_producto(id):
    sesion = Session()
    try:
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

            sesion.commit()
            flash('Producto actualizado correctamente.', 'success')
            return redirect(url_for('productos.ver_productos'))

        return render_template('producto/editar_producto.html', producto=producto)
    except Exception as e:
        sesion.rollback()
        flash(f'Error al actualizar producto: {str(e)}', 'warning')
        return redirect(url_for('productos.ver_productos'))
    finally:
        sesion.close()


# ❌ Eliminar producto
@productos_bp.route('/eliminar_producto/<int:id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_producto(id):
    sesion = Session()
    try:
        producto = sesion.query(Producto).filter_by(id=id).first()

        if not producto:
            flash('❌ Producto no encontrado.')
            return redirect(url_for('productos.ver_productos'))

        venta_asociada = sesion.query(DetalleVenta).filter_by(producto_id=id).first()
        if venta_asociada:
            flash(
                '⚠️ No se puede eliminar el producto porque ya ha sido vendido.',
                'warning'
            )
            return redirect(url_for('productos.ver_productos'))

        if producto.stock > 0:
            flash(
                '⚠️ No se puede eliminar un producto con stock mayor que cero.',
                'warning'
            )
            return redirect(url_for('productos.ver_productos'))

        sesion.delete(producto)
        sesion.commit()
        flash('✅ Producto eliminado correctamente.', 'success')
    except Exception as e:
        sesion.rollback()
        flash(f'❌ Error al eliminar el producto: {e}', 'warning')
    finally:
        sesion.close()

    return redirect(url_for('productos.ver_productos'))
