from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric, Boolean
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from flask import session, redirect, url_for, flash, request
import sqlite3

# 🚀 Configuración de la base de datos / Database configuration
# Engine permite a SALAlchemy comunicarse con la base de datos
engine = create_engine('sqlite:///database/productos.db', connect_args={'check_same_thread': False})
#Creamos la sesion, lo que nos permite realizar transacciones dentro de la base de datos
Session = sessionmaker(bind=engine)
sesion = Session()
#Esta clase se encarga de mapear la info de las clases en las que hereda y vincular su información a tablas de la base de datos
Base = declarative_base()

# 🔧 MODELOS DE LA BASE DE DATOS / DATABASE MODELS

# ▶️ Categoría de productos / Product category
class Categoria(Base):
    __tablename__ = "Categoria"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)

# ▶️ Proveedores / Suppliers
class Proveedor(Base):
    __tablename__ = "Proveedor"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    contacto = Column(String(150))
    telefono = Column(String(20))
    email = Column(String(150), unique=True)
    cif = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(200))

# ▶️ Productos / Products
class Producto(Base):
    __tablename__ = "Producto"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    descripcion = Column(Text)
    categoria_id = Column(Integer, ForeignKey('Categoria.id'), nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, default=0)
    cantidad_total = Column(Integer, default=30)
    fecha_creacion = Column(DateTime, default=func.now())

    categoria = relationship('Categoria', backref=backref('productos', lazy=True))
    ventas = relationship("DetalleVenta", back_populates="producto")

# ▶️ Clientes / Clients
class Cliente(Base):
    __tablename__ = "Cliente"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(150), unique=True, nullable=False)
    contacto = Column(String(150))
    telefono = Column(String(20))
    email = Column(String(150), unique=True)
    dni = Column(String(20), unique=True, nullable=False)
    direccion = Column(String(200))
    ventas = relationship("Venta", back_populates="cliente")

# ▶️ Ventas / Sales
class Venta(Base):
    __tablename__ = "Venta"
    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("Cliente.id"), nullable=False)
    ubicacion_id = Column(Integer, ForeignKey("Ubicacion.id"))  # NUEVO
    fecha = Column(DateTime, default=func.now())
    total = Column(Numeric(10, 2), nullable=False)
    descuento = Column(Numeric(10, 2), default=Decimal('0.00'))
    total_final = Column(Numeric(10, 2), nullable=False)
    pagado = Column(Boolean, default=False)

    cliente = relationship("Cliente", back_populates="ventas")
    detalles = relationship("DetalleVenta", back_populates="venta")
    ubicacion = relationship("Ubicacion")  # NUEVO

# ▶️ Detalle de cada producto en una venta / Sale item detail
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

# ▶️ Compras a proveedores / Purchases from suppliers
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

# 🚪 Crear las tablas al ejecutar / Create tables on script load
Base.metadata.create_all(engine)

# 🧍 Modelo de Usuario / User model
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario = Column(String(150), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)  # contraseña hasheada
    rol = Column(String(50), nullable=False, default="cliente")


# 🔐 Registrar nuevo usuario / Register new user
# Devuelve False si ya existe el usuario / Returns False if username exists
def register_user(usuario, contrasena, rol='cliente'):
    existente = sesion.query(Usuario).filter_by(usuario=usuario).first()
    if existente:
        return False
    hashed_pw = generate_password_hash(contrasena)
    nuevo = Usuario(usuario=usuario, contrasena=hashed_pw, rol=rol)
    sesion.add(nuevo)
    sesion.commit()
    return True


# 🔎 Verificar usuario y contraseña / Verify username and password
def verify_user(usuario, contrasena):
    user = sesion.query(Usuario).filter_by(usuario=usuario).first()
    if user and check_password_hash(user.contrasena, contrasena):
        return {'id': user.id, 'usuario': user.usuario, 'rol': user.rol}
    return None


# 🔍 Obtener usuario por nombre / Get user by username
def get_user_by_username(usuario):
    return sesion.query(Usuario).filter_by(usuario=usuario).first()


# 🔒 Decorador para rutas protegidas / Require login to access route
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario' not in session:
            flash('Por favor, inicie sesión para acceder a esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 🔒 Decorador para roles / Require specific role to access route
def rol_requerido(rol_permitido):
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            if 'usuario' not in session:
                flash('Debes iniciar sesión primero.', 'error')
                return redirect(url_for('login'))

            if session.get('rol') != rol_permitido:
                flash('No tienes permisos para acceder a esta página.', 'error')
                return redirect(request.referrer or url_for('index'))
            return f(*args, **kwargs)
        return funcion_decorada
    return decorador

# 👤 Crear usuarios por defecto / Create default users
# Se ejecuta desde main.py o desde este script si es principal

def crear_usuarios_por_defecto():
    admin_creado = register_user("jcm", "1234", "admin")
    cliente_creado = register_user("cliente", "1234", "cliente")

    if admin_creado:
        print("\u2705 Usuario admin creado.")
    else:
        print("\u26a0\ufe0f El usuario admin ya existe.")

    if cliente_creado:
        print("\u2705 Usuario cliente creado.")
    else:
        print("\u26a0\ufe0f El usuario cliente ya existe.")




#Ubicacion de las tiendas
class Ubicacion(Base):
    __tablename__ = "Ubicacion"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100), unique=True, nullable=False)

class StockPorUbicacion(Base):
    __tablename__ = "StockPorUbicacion"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey("Producto.id"), nullable=False)
    ubicacion_id = Column(Integer, ForeignKey("Ubicacion.id"), nullable=False)
    cantidad = Column(Integer, default=0)

    producto = relationship("Producto", backref="ubicaciones_stock")
    ubicacion = relationship("Ubicacion", backref="stock_producto")

# ⚡ Ejecutar solo si este archivo se ejecuta directamente / Run only if this file is executed directly
if __name__ == "__main__":
    crear_usuarios_por_defecto()
