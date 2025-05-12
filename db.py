from email.policy import default
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from decimal import Decimal
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, flash, request

# 🚀 Configuración de la base de datos
engine = create_engine('sqlite:///database/productos.db', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
sesion = Session()
Base = declarative_base()

# 🛠️ Modelos de la base de datos
class Categoria(Base):
    __tablename__ = "Categoria"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)

class Proveedor(Base):
    __tablename__ = "Proveedor"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    contacto = Column(String(150))
    telefono = Column(String(20))
    email = Column(String(150), unique=True)
    cif = Column(String(20), unique=True, nullable=False)  # Añadido CIF/DNI obligatorio
    direccion = Column(String(200))                        # Añadida Dirección

class Producto(Base):
    __tablename__ = "Producto"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey('Categoria.id'), nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    cantidad_total = Column(Integer, default=30)
    proveedor_id = Column(Integer, ForeignKey('Proveedor.id'), nullable=False)
    fecha_creacion = Column(DateTime, default=func.now())

    categoria = relationship('Categoria', backref=backref('productos', lazy=True))
    proveedor = relationship('Proveedor', backref=backref('productos', lazy=True))
    ventas = relationship("DetalleVenta", back_populates="producto")

class Cliente(Base):
    __tablename__ = "Cliente"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    contacto = Column(String(150))
    telefono = Column(String(20))
    email = Column(String(150), unique=True)
    dni = Column(String(20), unique=True, nullable=False)    # ← Añadido DNI obligatorio
    direccion = Column(String(200))                         # ← Añadida dirección opcional
    ventas = relationship("Venta", back_populates="cliente")


class Venta(Base):
    __tablename__ = "Venta"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("Cliente.id"), nullable=False)
    fecha = Column(DateTime, default=func.now())
    total = Column(Numeric(10, 2), nullable=False)
    descuento = Column(Numeric(10, 2), default=Decimal('0.00'))
    total_final = Column(Numeric(10, 2), nullable=False)
    pagado = Column(Boolean, default=False)

    cliente = relationship("Cliente", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta")

class DetalleVenta(Base):
    __tablename__ = "DetalleVenta"
    id = Column(Integer, primary_key=True)
    venta_id = Column(Integer, ForeignKey("Venta.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("Producto.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)

    venta = relationship("Venta", back_populates="detalles")
    producto = relationship("Producto", back_populates="ventas")

class Compra(Base):
    __tablename__ = "Compra"
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('Producto.id'), nullable=False)
    proveedor_id = Column(Integer, ForeignKey('Proveedor.id'), nullable=False)
    precio = Column(Numeric(10, 2), nullable=False)
    cantidad = Column(Integer, nullable=False)
    total = Column(Numeric(10, 2), nullable=False)
    fecha = Column(DateTime, default=func.now())

    producto = relationship("Producto")
    proveedor = relationship("Proveedor")

# 🚀 Crear las tablas principales en la base de datos
Base.metadata.create_all(engine)

# 🔐 Crear tabla de usuarios (sqlite3 "puro")
def create_user_table():
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL DEFAULT 'cliente'
        )
    ''')
    conn.commit()
    conn.close()

create_user_table()

# 🔐 Funciones de gestión de usuarios
def register_user(usuario, contrasena, rol='cliente'):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash(contrasena)
        cursor.execute('INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)', (usuario, hashed_pw, rol))
        conn.commit()
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
    return True

def verify_user(usuario, contrasena):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], contrasena):
        return {'id': user[0], 'usuario': user[1], 'rol': user[3]}
    return None

def get_user_by_username(usuario):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario,))
    user = cursor.fetchone()
    conn.close()
    return user

# 🎯 Decoradores para proteger rutas en Flask
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, inicie sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def rol_requerido(rol_permitido):
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            if 'usuario' not in session:
                flash('Debes iniciar sesión primero.', 'error')
                return redirect(url_for('login_bp.login'))

            if session.get('rol') != rol_permitido:
                flash('No tienes permisos para acceder a esta página.', 'error')
                return redirect(request.referrer or url_for('index'))
            return f(*args, **kwargs)
        return funcion_decorada
    return decorador


# Funcion crear usuario
def crear_usuarios_por_defecto():
    admin_creado = register_user("jcm", "1234", "admin")
    cliente_creado = register_user("cliente", "1234", "cliente")

    if admin_creado:
        print("✅ Usuario admin creado.")
    else:
        print("⚠️ El usuario admin ya existe.")

    if cliente_creado:
        print("✅ Usuario cliente creado.")
    else:
        print("⚠️ El usuario cliente ya existe.")


# 👤 Crear usuarios por defecto SOLO si ejecutamos db.py directamente
if __name__ == "__main__":
    usuario_admin = register_user("jcm", "1234", "admin")
    usuario_cliente = register_user("cliente", "cliente123", "cliente")

    if usuario_admin:
        print("Usuario admin creado correctamente.")
    else:
        print("El usuario admin ya existe.")

    if usuario_cliente:
        print("Usuario cliente creado correctamente.")
    else:
        print("El usuario cliente ya existe.")
