import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from db import engine, Base, verify_user, sesion, crear_usuarios_por_defecto, Cliente, login_required, Ubicacion, Venta

# Importar Blueprints (rutas organizadas)
from routes.index import index_bp
from routes.productos import productos_bp
from routes.proveedores import proveedores_bp
from routes.clientes import clientes_bp
from routes.ventas import ventas_bp
from routes.compras import compras_bp
from routes.graficas import graficas_bp
from routes.graficas_py import graficas_py_bp
from routes.almacenes import almacenes_bp


# 🚀 Crear aplicación Flask
# ✨ Create the Flask app
app = Flask(__name__)
app.config['DEBUG'] = True
app.secret_key = 'clavesecreta'  # Clave para manejar sesiones / Secret key for session handling

# 📁 Verificar carpeta de base de datos
# ✏️ Check if database folder exists, otherwise create it
DB_DIR = os.path.join(os.path.dirname(__file__), "database")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

# 📊 Crear todas las tablas definidas en los modelos / Create DB tables from models
Base.metadata.create_all(engine)



# 🔓 Crear usuarios por defecto / Create default users (admin and client)
crear_usuarios_por_defecto()

# 🏠 Ruta principal de inicio / Main homepage route
@app.route('/')
def index():
    return render_template('index.html')

# 🔐 Ruta de inicio de sesión / Login route
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

# 🔒 Ruta para cerrar sesión / Logout route
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    session.pop('rol', None)
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))


# Paso 2: Inicializar ubicaciones por defecto en main.py
def crear_ubicaciones_por_defecto():
    ubicaciones = ["Almacén", "Oficina1 (Sevilla)", "Oficina2 (Madrid)", "Oficina3 (Valencia)"]
    for nombre in ubicaciones:
        if not sesion.query(Ubicacion).filter_by(nombre=nombre).first():
            sesion.add(Ubicacion(nombre=nombre))
    sesion.commit()

crear_ubicaciones_por_defecto()

# 📍 Registrar todos los Blueprints / Register all route modules
app.register_blueprint(index_bp)
app.register_blueprint(productos_bp)
app.register_blueprint(proveedores_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(ventas_bp)
app.register_blueprint(compras_bp)
app.register_blueprint(graficas_bp)
app.register_blueprint(graficas_py_bp)
app.register_blueprint(almacenes_bp)



# ▶️ Iniciar la aplicación si este archivo es el principal / Run the app if executed directly
if __name__ == '__main__':
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

