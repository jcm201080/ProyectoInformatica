from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Proveedor, Producto

proveedores_bp = Blueprint('proveedores', __name__)

@proveedores_bp.route('/proveedores')
def proveedores():
    proveedores = sesion.query(Proveedor).all()
    return render_template('proveedor/proveedor.html', proveedores=proveedores)

@proveedores_bp.route('/add_proveedor', methods=['POST'])
def add_proveedor():
    nombre = request.form['nombre']
    contacto = request.form['contacto']
    telefono = request.form['telefono']
    email = request.form['email']

    existe_proveedor = sesion.query(Proveedor).filter_by(nombre=nombre).first()
    if existe_proveedor:
        flash('Este proveedor ya existe.')
        return redirect(url_for('proveedores.proveedores'))

    nuevo_proveedor = Proveedor(nombre=nombre, contacto=contacto, telefono=telefono, email=email)

    try:
        sesion.add(nuevo_proveedor)
        sesion.commit()
        flash('Proveedor añadido correctamente.')
    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir proveedor: {str(e)}')

    return redirect(url_for('proveedores.proveedores'))

@proveedores_bp.route('/editar_proveedor/<int:id>', methods=['GET', 'POST'])
def editar_proveedor(id):
    proveedor = sesion.query(Proveedor).filter_by(id=id).first()

    if not proveedor:
        flash('Proveedor no encontrado.')
        return redirect(url_for('proveedores.proveedores'))

    if request.method == 'POST':
        proveedor.nombre = request.form['nombre']
        proveedor.contacto = request.form['contacto']
        proveedor.telefono = request.form['telefono']
        proveedor.email = request.form['email']

        try:
            sesion.commit()
            flash('Proveedor actualizado correctamente.')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al actualizar proveedor: {str(e)}')

        return redirect(url_for('proveedores.proveedores'))

    return render_template('proveedor/editar_proveedor.html', proveedor=proveedor)

@proveedores_bp.route('/eliminar_proveedor/<int:id>', methods=['POST'])
def eliminar_proveedor(id):
    proveedor = sesion.query(Proveedor).filter_by(id=id).first()

    if proveedor:
        try:
            productos_asociados = sesion.query(Producto).filter_by(proveedor_id=id).count()
            if productos_asociados > 0:
                flash('No se puede eliminar el proveedor porque tiene productos asociados.')
                return redirect(url_for('proveedores.proveedores'))

            sesion.delete(proveedor)
            sesion.commit()
            flash('Proveedor eliminado correctamente.')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al eliminar proveedor: {str(e)}')
    else:
        flash('Proveedor no encontrado.')

    return redirect(url_for('proveedores.proveedores'))

