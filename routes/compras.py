from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import (
    Session,
    Producto,
    Proveedor,
    login_required,
    rol_requerido,
    Compra,
    Ubicacion,
    StockPorUbicacion
)
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy import desc
from datetime import datetime

compras_bp = Blueprint('compras', __name__)


# 📅 Mostrar lista de compras con filtros y paginación
@compras_bp.route('/compras')
@login_required
def compras():
    sesion = Session()
    try:
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

        return render_template(
            "compras/compras.html",
            compras=compras,
            pagina=pagina,
            hay_anterior=hay_anterior,
            hay_siguiente=hay_siguiente,
            proveedor=proveedor,
            orden=orden,
            direccion=direccion
        )
    finally:
        sesion.close()


# 🛒 Registrar una nueva compra
@compras_bp.route('/nueva_compra', methods=['GET', 'POST'])
@login_required
def nueva_compra():
    sesion = Session()
    try:
        productos = sesion.query(Producto).all()
        proveedores = sesion.query(Proveedor).all()

        if request.method == "POST":
            producto_id = request.form["producto_id"]
            proveedor_id = request.form["proveedor_id"]

            try:
                precio = float(request.form["precio"])
                cantidad = int(request.form["cantidad"])
            except ValueError:
                flash(
                    "Precio o cantidad inválidos. Asegúrate de rellenar todos los campos.",
                    "error"
                )
                return redirect(url_for("compras.nueva_compra"))

            producto = sesion.get(Producto, producto_id)
            if not producto:
                flash("Producto no encontrado", "error")
                return redirect(url_for("compras.nueva_compra"))

            nuevo_stock = producto.stock + cantidad
            if nuevo_stock > producto.cantidad_total:
                flash(
                    f"¡Alerta! Capacidad máxima superada: {nuevo_stock}/{producto.cantidad_total} unidades. "
                    f"Has añadido {nuevo_stock - producto.cantidad_total} unidades de más.",
                    "warning"
                )
            else:
                flash("Compra dentro del límite de capacidad.", "info")

            producto.stock = nuevo_stock

            ubicacion_almacen = sesion.query(Ubicacion).filter_by(nombre="Almacén").first()

            try:
                stock_ubicacion = sesion.query(StockPorUbicacion).filter_by(
                    producto_id=producto.id,
                    ubicacion_id=ubicacion_almacen.id
                ).one()
                stock_ubicacion.cantidad += cantidad
            except NoResultFound:
                stock_ubicacion = StockPorUbicacion(
                    producto_id=producto.id,
                    ubicacion_id=ubicacion_almacen.id,
                    cantidad=cantidad
                )
                sesion.add(stock_ubicacion)

            nueva_compra = Compra(
                producto_id=producto_id,
                proveedor_id=proveedor_id,
                precio=precio,
                cantidad=cantidad,
                total=precio * cantidad
            )
            sesion.add(nueva_compra)
            sesion.commit()

            flash(
                f"Compra registrada. Stock actual: {producto.stock}/{producto.cantidad_total}",
                "success"
            )
            return redirect(url_for("compras.compras"))

        return render_template(
            "compras/nueva_compra.html",
            productos=productos,
            proveedores=proveedores
        )
    except Exception as e:
        sesion.rollback()
        flash(f"Error al registrar la compra: {str(e)}", "error")
        return redirect(url_for("compras.nueva_compra"))
    finally:
        sesion.close()


# ✏️ Editar una compra
@compras_bp.route('/compras/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin')
def editar_compra(id):
    sesion = Session()
    try:
        compra = sesion.get(Compra, id)
        proveedores = sesion.query(Proveedor).all()

        if request.method == 'POST':
            compra.proveedor_id = request.form['proveedor_id']
            compra.total = float(request.form['total'])
            compra.fecha = datetime.strptime(
                request.form['fecha'], '%Y-%m-%d'
            ).date()

            sesion.commit()
            flash('Compra actualizada correctamente ✅', 'success')
            return redirect(url_for('compras.compras'))

        return render_template(
            'compras/editar_compra.html',
            compra=compra,
            proveedores=proveedores
        )
    except Exception as e:
        sesion.rollback()
        flash(f'Error al actualizar la compra: {str(e)}', 'error')
        return redirect(url_for('compras.compras'))
    finally:
        sesion.close()


# 🗑️ Eliminar una compra
@compras_bp.route('/compras/eliminar/<int:id>', methods=['POST'])
@login_required
@rol_requerido('admin')
def eliminar_compra(id):
    sesion = Session()
    try:
        compra = sesion.get(Compra, id)
        if not compra:
            flash('Compra no encontrada.', 'error')
            return redirect(url_for('compras.compras'))

        sesion.delete(compra)
        sesion.commit()
        flash('Compra eliminada correctamente 🗑️', 'success')
    except Exception as e:
        sesion.rollback()
        flash(f'Error al eliminar la compra: {str(e)}', 'error')
    finally:
        sesion.close()

    return redirect(url_for('compras.compras'))
