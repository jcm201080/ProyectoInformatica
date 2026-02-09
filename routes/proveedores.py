from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import Session, Producto, Proveedor, login_required, rol_requerido

# 🔹 Blueprint de proveedores / Suppliers blueprint
proveedores_bp = Blueprint('proveedores', __name__)

# =====================================================
# 📋 Listar proveedores
# ES: Muestra un listado paginado de proveedores con
#     búsqueda por nombre o CIF y ordenación.
# EN: Displays a paginated supplier list with search
#     and sorting options.
# =====================================================
@proveedores_bp.route('/proveedores')
@login_required
def listar_proveedores():
    sesion = Session()
    try:
        nombre = request.args.get("nombre", "")
        pagina = int(request.args.get("pagina", 1))
        orden = request.args.get("orden", "id")
        direccion = request.args.get("direccion", "asc")
        por_pagina = 30

        query = sesion.query(Proveedor)

        if nombre:
            query = query.filter(
                (Proveedor.nombre.ilike(f"%{nombre}%")) |
                (Proveedor.cif.ilike(f"%{nombre}%"))
            )

        def aplicar_orden(campo):
            return campo.desc() if direccion == "desc" else campo.asc()

        if orden == "nombre":
            query = query.order_by(aplicar_orden(Proveedor.nombre))
        elif orden == "cif":
            query = query.order_by(aplicar_orden(Proveedor.cif))
        else:
            query = query.order_by(aplicar_orden(Proveedor.id))

        total = query.count()
        proveedores = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

        return render_template(
            "proveedores/proveedor.html",
            proveedores=proveedores,
            pagina=pagina,
            hay_anterior=pagina > 1,
            hay_siguiente=(pagina * por_pagina) < total,
            nombre=nombre,
            orden=orden,
            direccion=direccion
        )
    finally:
        sesion.close()


# =====================================================
# 🆕 Formulario nuevo proveedor
# ES: Muestra el formulario para crear un proveedor.
# EN: Shows the form to create a new supplier.
# =====================================================
@proveedores_bp.route('/proveedores/nuevo')
@login_required
@rol_requerido('admin')
def formulario_proveedor():
    return render_template('proveedores/agregar_proveedor.html')


# =====================================================
# 💾 Crear proveedor
# ES: Inserta un nuevo proveedor validando duplicados.
# EN: Inserts a new supplier with duplicate validation.
# =====================================================
@proveedores_bp.route('/add_proveedor', methods=['POST'])
@login_required
@rol_requerido('admin')
def add_proveedor():
    sesion = Session()
    try:
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        email = request.form['email']
        cif = request.form['cif']
        direccion = request.form['direccion']

        existe = sesion.query(Proveedor).filter(
            (Proveedor.nombre == nombre) | (Proveedor.cif == cif)
        ).first()

        if existe:
            flash('Este proveedor ya existe (por nombre o CIF).', 'warning')
            return redirect(url_for('proveedores.listar_proveedores'))

        nuevo_proveedor = Proveedor(
            nombre=nombre,
            contacto=contacto,
            telefono=telefono,
            email=email,
            cif=cif,
            direccion=direccion
        )

        sesion.add(nuevo_proveedor)
        sesion.commit()
        flash('Proveedor añadido correctamente.', 'success')

    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir proveedor: {str(e)}', 'danger')
    finally:
        sesion.close()

    return redirect(url_for('proveedores.listar_proveedores'))


# =====================================================
# ✏️ Editar proveedor
# ES: Permite modificar los datos de un proveedor.
# EN: Allows editing an existing supplier.
# =====================================================
@proveedores_bp.route('/editar_proveedor/<int:id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin')
def editar_proveedor(id):
    sesion = Session()
    try:
        proveedor = sesion.query(Proveedor).get(id)

        if not proveedor:
            flash('Proveedor no encontrado.', 'warning')
            return redirect(url_for('proveedores.listar_proveedores'))

        if request.method == 'POST':
            proveedor.nombre = request.form['nombre']
            proveedor.contacto = request.form['contacto']
            proveedor.telefono = request.form['telefono']
            proveedor.email = request.form['email']
            proveedor.cif = request.form['cif']
            proveedor.direccion = request.form['direccion']

            sesion.commit()
            flash('Proveedor actualizado correctamente.', 'success')
            return redirect(url_for('proveedores.listar_proveedores'))

        return render_template(
            'proveedores/editar_proveedor.html',
            proveedor=proveedor
        )

    except Exception as e:
        sesion.rollback()
        flash(f'Error al actualizar proveedor: {str(e)}', 'danger')
        return redirect(url_for('proveedores.listar_proveedores'))
    finally:
        sesion.close()


# =====================================================
# 🗑️ Eliminar proveedor
# ES: Elimina un proveedor solo si no tiene productos.
# EN: Deletes a supplier only if no products are linked.
# =====================================================
@proveedores_bp.route('/eliminar_proveedor/<int:id>', methods=['POST'])
@login_required
@rol_requerido('admin')
def eliminar_proveedor(id):
    sesion = Session()
    try:
        proveedor = sesion.query(Proveedor).get(id)

        if not proveedor:
            flash('Proveedor no encontrado.', 'warning')
            return redirect(url_for('proveedores.listar_proveedores'))

        productos_asociados = sesion.query(Producto).filter_by(proveedor_id=id).count()
        if productos_asociados > 0:
            flash(
                'No se puede eliminar el proveedor porque tiene productos asociados.',
                'warning'
            )
            return redirect(url_for('proveedores.listar_proveedores'))

        sesion.delete(proveedor)
        sesion.commit()
        flash('Proveedor eliminado correctamente.', 'success')

    except Exception as e:
        sesion.rollback()
        flash(f'Error al eliminar proveedor: {str(e)}', 'danger')
    finally:
        sesion.close()

    return redirect(url_for('proveedores.listar_proveedores'))
