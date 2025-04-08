from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Proveedor, Producto,Cliente

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes')
def clientes():
    clientes = sesion.query(Cliente).all()
    return render_template('cliente/clientes.html', clientes=clientes)

@clientes_bp.route('/add_cliente', methods=['POST'])
def add_cliente():
    nombre = request.form['nombre']
    contacto = request.form['contacto']
    telefono = request.form['telefono']
    email = request.form['email']

    existe_cliente = sesion.query(Cliente).filter_by(nombre=nombre).first()
    if existe_cliente:
        flash('Este cliente ya existe.')
        return redirect(url_for('clientes.clientes'))

    nuevo_cliente = Cliente(nombre=nombre, contacto=contacto, telefono=telefono, email=email)

    try:
        sesion.add(nuevo_cliente)
        sesion.commit()
        flash('Cliente añadido correctamente.')
    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir cliente: {str(e)}')

    return redirect(url_for('clientes.clientes'))


@clientes_bp.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    cliente = sesion.query(Cliente).get(id)
    if not cliente:
        flash('Cliente no encontrado.')
        return redirect(url_for('clientes.clientes'))

    if request.method == 'POST':
        cliente.nombre = request.form['nombre']
        cliente.contacto = request.form['contacto']
        cliente.telefono = request.form['telefono']
        cliente.email = request.form['email']

        try:
            sesion.commit()
            flash('Cliente actualizado correctamente.')
            return redirect(url_for('clientes.clientes'))
        except Exception as e:
            sesion.rollback()
            flash(f'Error al actualizar cliente: {str(e)}')

    return render_template('cliente/editar_cliente.html', cliente=cliente)


@clientes_bp.route('/eliminar_cliente/<int:id>', methods=['POST'])
def eliminar_cliente(id):
    cliente = sesion.query(Cliente).get(id)
    if cliente:
        try:
            sesion.delete(cliente)
            sesion.commit()
            flash('Cliente eliminado correctamente.')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al eliminar cliente: {str(e)}')
    return redirect(url_for('clientes.clientes'))
