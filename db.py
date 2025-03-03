from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

# Conexión a SQLite
engine = create_engine('sqlite:///database/productos.db',
                       connect_args={'check_same_thread': False})

Session = sessionmaker(bind=engine)
sesion = Session()
Base = declarative_base()

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

class Venta(Base):
    __tablename__ = "Venta"
    id = Column(Integer, primary_key=True)
    producto_id = Column(Integer, ForeignKey('Producto.id'), nullable=True)
    cantidad = Column(Integer, nullable=False)
    fecha_venta = Column(DateTime, default=func.current_timestamp())

    producto = relationship('Producto', backref=backref('ventas', lazy=True))


#Crear Usuarios
import sqlite3

# Función para conectar a la base de datos
def connect_db():
    return sqlite3.connect("usuarios.db")

# Función para crear la tabla de usuarios (si no existe)
def create_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Función para registrar un nuevo usuario
def register_user(usuario, contrasena):
    conn = connect_db()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO usuarios (usuario, contrasena)
            VALUES (?, ?)
        ''', (usuario, contrasena))
        conn.commit()
    except sqlite3.IntegrityError:
        return False  # Si ya existe el usuario
    conn.close()
    return True

# Función para verificar si el usuario existe
def verify_user(usuario, contrasena):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM usuarios WHERE usuario = ? AND contrasena = ?
    ''', (usuario, contrasena))
    user = cursor.fetchone()
    conn.close()
    return user is not None


if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tablas creadas exitosamente")