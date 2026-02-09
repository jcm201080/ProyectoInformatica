from flask import Blueprint, render_template, request, redirect, url_for, flash
from db import Session, Cliente, login_required, rol_requerido

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/clientes')
@login_required
def clientes():
    sesion = Session()
    try:
        nombre = request.args.get("nombre")
        pagina = int(request.args.get("pagina", 1))
        orden = request.args.get("orden", "id")
        direccion = request.args.get("direccion", "asc")
        por_pagina = 30

        query = sesion.query(Cliente)

        if nombre:
            query = query.filter(
                (Cliente.nombre.ilike(f"%{nombre}%")) |
                (Cliente.contacto.ilike(f"%{nombre}%"))
            )

        def aplicar_orden(campo):
            return campo.desc() if direccion == "desc" else campo.asc()

        if orden == "nombre":
            query = query.order_by(aplicar_orden(Cliente.nombre))
        elif orden == "contacto":
            query = query.order_by(aplicar_orden(Cliente.contacto))
        else:
            query = query.order_by(aplicar_orden(Cliente.id))

        total_clientes = query.count()
        clientes = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

        hay_anterior = pagina > 1
        hay_siguiente = (pagina * por_pagina) < total_clientes

        return render_template(
            "cliente/clientes.html",
            clientes=clientes,
            pagina=pagina,
            hay_anterior=hay_anterior,
            hay_siguiente=hay_siguiente,
            nombre=nombre,
            orden=orden,
            direccion=direccion
        )
    finally:
        sesion.close()


@clientes_bp.route('/agregar_cliente', methods=['GET'])
@rol_requerido('admin')
def agregar_cliente():
    return render_template('cliente/agregar_cliente.html')


@clientes_bp.route('/add_cliente', methods=['POST'])
@rol_requerido('admin')
def add_cliente():
    sesion = Session()
    try:
        nombre = request.form['nombre']
        contacto = request.form['contacto']
        telefono = request.form['telefono']
        email = request.form['email']
        dni = request.form['dni']
        direccion = request.form['direccion']

        existe_cliente = sesion.query(Cliente).filter(
            (Cliente.nombre == nombre) | (Cliente.dni == dni)
        ).first()

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

        sesion.add(nuevo_cliente)
        sesion.commit()
        flash('Cliente añadido correctamente.')
        return redirect(url_for('clientes.clientes'))
    except Exception as e:
        sesion.rollback()
        flash(f'Error al añadir cliente: {str(e)}')
        return redirect(url_for('clientes.clientes'))
    finally:
        sesion.close()


@clientes_bp.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
@rol_requerido('admin')
def editar_cliente(id):
    sesion = Session()
    try:
        cliente = sesion.get(Cliente, id)
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

            sesion.commit()
            flash('Cliente actualizado correctamente.')
            return redirect(url_for('clientes.clientes'))

        return render_template('cliente/editar_cliente.html', cliente=cliente)
    except Exception as e:
        sesion.rollback()
        flash(f'Error al actualizar cliente: {str(e)}')
        return redirect(url_for('clientes.clientes'))
    finally:
        sesion.close()


@clientes_bp.route('/eliminar_cliente/<int:id>', methods=['POST'])
@rol_requerido('admin')
def eliminar_cliente(id):
    sesion = Session()
    try:
        cliente = sesion.query(Cliente).filter_by(id=id).first()

        if not cliente:
            flash('Cliente no encontrado.', 'warning')
            return redirect(url_for('clientes.clientes'))

        sesion.delete(cliente)
        sesion.commit()
        flash('✅ Cliente eliminado correctamente.', 'success')
    except Exception as e:
        sesion.rollback()
        if "NOT NULL constraint failed: Venta.cliente_id" in str(e):
            flash('❌ No se puede eliminar el cliente porque tiene ventas asociadas.', 'warning')
        else:
            flash(f'⚠️ Error inesperado al eliminar cliente: {str(e)}', 'danger')
    finally:
        sesion.close()

    return redirect(url_for('clientes.clientes'))
