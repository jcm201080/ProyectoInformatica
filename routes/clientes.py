from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import sesion, Producto, Proveedor, login_required, rol_requerido, Cliente

# 🔵 Definir el blueprint
clientes_bp = Blueprint('clientes', __name__)

# 📋 Ruta para listar clientes
@clientes_bp.route('/clientes')
@login_required
def clientes():
    clientes = sesion.query(Cliente).all()
    return render_template('cliente/clientes.html', clientes=clientes)

# ➕ Ruta para mostrar formulario de nuevo cliente
@clientes_bp.route('/agregar_cliente', methods=['GET'])
@rol_requerido('admin')
def agregar_cliente():
    return render_template('cliente/agregar_cliente.html')

# ➕ Ruta para añadir cliente a la base de datos
@clientes_bp.route('/add_cliente', methods=['POST'])
@rol_requerido('admin')
def add_cliente():
    nombre = request.form['nombre']
    contacto = request.form['contacto']
    telefono = request.form['telefono']
    email = request.form['email']
    dni = request.form['dni']
    direccion = request.form['direccion']

    existe_cliente = sesion.query(Cliente).filter((Cliente.nombre == nombre) | (Cliente.dni == dni)).first()
    if existe_cliente:
        flash('Este cliente ya existe (por nombre o DNI).')
        return redirect(url_for('clientes.clientes'))

    nuevo_cliente = Cliente(
        nombre=nombre,
        contacto=contacto,
        telefono=telefono,
        email=email,
        dni=dni,
        direccion=direccion
    )

    try:
        sesion.add(nuevo_cliente)
        sesion.commit()
        flash('Cliente añadido correctamente.')
    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir cliente: {str(e)}')

    return redirect(url_for('clientes.clientes'))

# 🛠 Ruta para editar cliente
@clientes_bp.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@rol_requerido('admin')
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
        cliente.dni = request.form['dni']
        cliente.direccion = request.form['direccion']

        try:
            sesion.commit()
            flash('Cliente actualizado correctamente.')
            return redirect(url_for('clientes.clientes'))
        except Exception as e:
            sesion.rollback()
            flash(f'Error al actualizar cliente: {str(e)}')

    return render_template('cliente/editar_cliente.html', cliente=cliente)

# ❌ Ruta para eliminar cliente
@clientes_bp.route('/eliminar_cliente/<int:id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_cliente(id):
    cliente = sesion.query(Cliente).filter_by(id=id).first()

    if cliente:
        try:
            sesion.delete(cliente)
            sesion.commit()
            flash('Cliente eliminado correctamente.', 'success')
        except Exception as e:
            sesion.rollback()
            flash(f'Error al eliminar cliente: {str(e)}', 'danger')
    else:
        flash('Cliente no encontrado.', 'warning')

    return redirect(url_for('clientes.clientes'))
