from http.cookiejar import debug
import os.path
from db import engine, Base, Producto, sesion
from flask import Flask, render_template, request, redirect, url_for


#Creamos la carpeta database si no exicte
DB_DIR = os.path.join(os.path.dirname(__file__),"database")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)
# Crear la base de datos si no existe
Base.metadata.create_all(engine)


from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/producto')
def producto():
    return render_template('producto.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    nombre = request.form['nombre']
    descripcion = request.form['descripcion']
    precio = float(request.form['precio'])
    stock = int(request.form['stock'])
    proveedor_id = int(request.form['proveedor_id'])

    nuevo_producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=precio,
        stock=stock,
        proveedor_id=proveedor_id
    )

    sesion.add(nuevo_producto)
    sesion.commit()

    return redirect(url_for('index'))

if __name__== '__main__':
    app.run(debug=True)