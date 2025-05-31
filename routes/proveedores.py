from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor, login_required, rol_requerido

# 🔹 Definir blueprint para proveedores / Define blueprint for suppliers
proveedores_bp = Blueprint('proveedores', __name__)

# 📋 Listar proveedores con filtros y paginación / List suppliers with filters and pagination
@proveedores_bp.route('/proveedores')
@login_required
def listar_proveedores():
    nombre = request.args.get("nombre")
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

    hay_anterior = pagina > 1
    hay_siguiente = (pagina * por_pagina) < total

    return render_template("proveedores/proveedor.html",
        proveedores=proveedores,
        pagina=pagina,
        hay_anterior=hay_anterior,
        hay_siguiente=hay_siguiente,
        nombre=nombre,
        orden=orden,
        direccion=direccion
    )

# 🆕 Formulario para agregar proveedor (solo admin) / Show form to add new supplier (admin only)
@proveedores_bp.route('/proveedores/nuevo')
@login_required
@rol_requerido('admin')
def formulario_proveedor():
    return render_template('proveedores/agregar_proveedor.html')

# 💾 Procesar nuevo proveedor / Process new supplier form
@proveedores_bp.route('/add_proveedor', methods=['POST'])
@login_required
@rol_requerido('admin')
def add_proveedor():
    nombre = request.form['nombre']
    contacto = request.form['contacto']
    telefono = request.form['telefono']
    email = request.form['email']
    cif = request.form['cif']
    direccion = request.form['direccion']

    # 🔍 Validar duplicado / Check for duplicate supplier
    existe_proveedor = sesion.query(Proveedor).filter(
        (Proveedor.nombre == nombre) | (Proveedor.cif == cif)
    ).first()
    if existe_proveedor:
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

    try:
        sesion.add(nuevo_proveedor)
        sesion.commit()
        flash('Proveedor añadido correctamente.', 'success')
    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir proveedor: {str(e)}', 'danger')

    return redirect(url_for('proveedores.listar_proveedores'))

# ✏️ Editar proveedor (solo admin) / Edit existing supplier (admin only)
@proveedores_bp.route('/editar_proveedor/<int:id>', methods=['GET', 'POST'])
@login_required
@rol_requerido('admin')
def editar_proveedor(id):
    proveedor = sesion.query(Proveedor).filter_by(id=id).first()

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

        try:
            sesion.commit()
            flash('Proveedor actualizado correctamente.', 'success')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}', 'danger')

        return redirect(url_for('proveedores.listar_proveedores'))

    return render_template('proveedores/editar_proveedor.html', proveedor=proveedor)

# 🗑️ Eliminar proveedor (si no tiene productos) / Delete supplier (if no products assigned)
@proveedores_bp.route('/eliminar_proveedor/<int:id>', methods=['POST'])
@login_required
@rol_requerido('admin')
def eliminar_proveedor(id):
    proveedor = sesion.query(Proveedor).filter_by(id=id).first()

    if proveedor:
        try:
            productos_asociados = sesion.query(Producto).filter_by(proveedor_id=id).count()
            if productos_asociados > 0:
                flash('No se puede eliminar el proveedor porque tiene productos asociados.', 'warning')
                return redirect(url_for('proveedores.listar_proveedores'))

            sesion.delete(proveedor)
            sesion.commit()
            flash('Proveedor eliminado correctamente.', 'success')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al eliminar proveedor: {str(e)}', 'danger')
    else:
        flash('Proveedor no encontrado.', 'warning')

    return redirect(url_for('proveedores.listar_proveedores'))
