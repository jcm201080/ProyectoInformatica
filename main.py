import os
from flask import Flask, render_template, request, redirect, url_for, session, flash

from db import engine, Base, Proveedor, Venta
from routes.index import index_bp
from routes.productos import productos_bp
from routes.proveedores import proveedores_bp
from routes.clientes import clientes_bp
from routes.ventas import ventas_bp
from db import create_user_table, verify_user,sesion, Cliente, login_required


app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = 'clavesecreta'

# Creamos la carpeta database si no existe
DB_DIR = os.path.join(os.path.dirname(__file__), "database")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Crear la base de datos si no existe
Base.metadata.create_all(engine)

@app.route('/')
def index():
    return render_template('index.html')


# Ruta para el login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        contrasena = request.form['contrasena']
        user = verify_user(usuario, contrasena)

        if user:
            session['usuario'] = usuario
            session['rol'] = user['rol']
            flash('Inicio de sesión exitoso', 'success')

            # Si el usuario intentaba acceder a una página restringida, redirigir a esa página
            next_page = request.args.get('next')  # Obtener la URL de la página que intentaba acceder
            return redirect(next_page or url_for('index'))  # Redirigir a la página solicitada o al inicio

        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')


#Restringir el acceso a las rutas protegidas

#Restringir a productos, Si rol = clientes solo la puede ver, si es admin puede añadir



#Restringir el acceso a las rutas protegidas


#Acceso a proveedores, pueden etrar todos los que esten registrados independientemente del rol
@app.route('/proveedores')
@login_required
def proveedores():
    # 🔍 Aquí deberías recuperar los clientes desde la base de datos
    proveedores = sesion.query(Proveedor).all()
    return render_template('proveedor/proveedor.html', proveedores=proveedores)

#Acceso a clientes, pueden etrar todos los que esten registrados independientemente del rol
@app.route('/clientes')
@login_required
def cliente():
    # 🔍 Aquí deberías recuperar los clientes desde la base de datos
    clientes = sesion.query(Cliente).all()
    return render_template('cliente/clientes.html',clientes=clientes)

#Acceso a Ventas, pueden etrar todos los que esten registrados independientemente del rol
@app.route('/ventas')
@login_required
def ventas():
    # 🔍 Aquí deberías recuperar los clientes desde la base de datos
    ventas = sesion.query(Venta).all()
    return render_template('ventas/ventas.html',ventas=ventas)





#Cierre de sesion
@app.route('/logout')
def logout():
    session.pop('usuario', None)  # Eliminar el usuario de la sesión
    session.pop('rol', None)  # Eliminar el rol de la sesión
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))  # Redirigir al índice después de cerrar sesión








app.secret_key = 'clavesecreta'  # Asegúrate de tener una clave secreta configurada


# Llamar a la función para crear la tabla de usuarios
create_user_table()

# Registramos los módulos de rutas
app.register_blueprint(index_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(proveedores_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(ventas_bp)  # <-- Registra el Blueprint de ventas

if __name__ == '__main__':
    app.run(debug=True)
