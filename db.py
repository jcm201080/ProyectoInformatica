from email.policy import default

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from decimal import Decimal
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, flash

# Conexión a SQLite (unificada para productos y usuarios en la misma BD)
engine = create_engine('sqlite:///database/productos.db', connect_args={'check_same_thread': False})
Session = sessionmaker(bind=engine)
sesion = Session()
Base = declarative_base()

# Definición de tablas
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

class Producto(Base):
    __tablename__ = "Producto"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey('Categoria.id'), nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    proveedor_id = Column(Integer, ForeignKey('Proveedor.id'), nullable=False)
    fecha_creacion = Column(DateTime, default=func.current_timestamp())

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
    ventas = relationship("Venta", back_populates="cliente")

class Venta(Base):
    __tablename__ = "Venta"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("Cliente.id"), nullable=False)
    fecha = Column(DateTime, default=func.current_timestamp())
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

# Creación de tabla de usuarios con rol
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

# Función para registrar un usuario con hash de contraseña
def register_user(usuario, contrasena, rol='cliente'):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    try:
        hashed_pw = generate_password_hash(contrasena)
        cursor.execute('''INSERT INTO usuarios (usuario, contrasena, rol) VALUES (?, ?, ?)''',
                       (usuario, hashed_pw, rol))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # Usuario ya existe
    finally:
        conn.close()
    return True


# Función para verificar usuario y obtener el rol
def verify_user(usuario, contrasena):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM usuarios WHERE usuario = ?''', (usuario,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], contrasena):
        return {'id': user[0], 'usuario': user[1], 'rol': user[3]}
    return None

# Función para obtener usuario por nombre
def get_user_by_username(usuario):
    conn = sqlite3.connect("database/productos.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM usuarios WHERE usuario = ?''', (usuario,))
    user = cursor.fetchone()
    conn.close()
    return user


from db import register_user  # Asegúrate de importar la función correcta

# Crear usuarios con diferentes roles
usuario_admin = register_user("admin", "admin123", "admin")
usuario_cliente = register_user("cliente1", "cliente123", "cliente")
usuario_vendedor = register_user("vendedor1", "123", "vendedor")

# Verificar si los usuarios fueron creados
if usuario_admin:
    print("Usuario admin creado correctamente.")
else:
    print("El usuario admin ya existe.")

if usuario_cliente:
    print("Usuario cliente creado correctamente.")
else:
    print("El usuario cliente ya existe.")

if usuario_vendedor:
    print("Usuario vendedor creado correctamente.")
else:
    print("El usuario vendedor ya existe.")





#funcion para usuarios registrados (cualquiera) si no estar registrado te manda a login (primer acceso)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, inicie sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



if __name__ == "__main__":
    Base.metadata.create_all(engine)
    create_user_table()
    print("Base de datos y tablas creadas exitosamente.")