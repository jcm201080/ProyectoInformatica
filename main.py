import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from sqlalchemy.orm import joinedload
from db import engine, Base, create_user_table, verify_user, sesion, crear_usuarios_por_defecto


# Modelos para login
from db import Cliente

# Decorador personalizado
from db import login_required
from routes.graficas_py import graficas_py_bp

# Blueprints (rutas)
from routes.index import index_bp
from routes.productos import productos_bp
from routes.proveedores import proveedores_bp
from routes.clientes import clientes_bp
from routes.ventas import ventas_bp
from routes.compras import compras_bp
from routes.graficas import graficas_bp  # <-- IMPORTACIÓN SOLO DESPUÉS DE DEFINIR TODAS LAS RUTAS
from routes.graficas_py import graficas_py_bp

# App Flask
app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = 'clavesecreta'

# Crear carpeta para la base de datos si no existe
DB_DIR = os.path.join(os.path.dirname(__file__), "database")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# Crear todas las tablas
Base.metadata.create_all(engine)

# Crear tabla de usuarios si no existe
create_user_table()

#Crear usuarios y cliente
crear_usuarios_por_defecto()

# Ruta principal
@app.route('/')
def index():
    return render_template('index.html')

# Ruta de login
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
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')

    return render_template('login.html')

# Cierre de sesión
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

# Registro de rutas (blueprints)
app.register_blueprint(index_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(proveedores_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(graficas_bp)
app.register_blueprint(graficas_py_bp)

# Iniciar la app
if __name__ == '__main__':
    app.run(debug=True)
