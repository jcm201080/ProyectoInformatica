from faker import Faker
import random
from decimal import Decimal
from datetime import datetime, timedelta

from db import sesion, Cliente, Producto, Venta, DetalleVenta, Proveedor, Compra

fake = Faker('es_ES')


def crear_proveedores(n=5):
    for _ in range(n):
        proveedor = Proveedor(
            nombre=fake.company(),
            contacto=fake.name(),
            telefono=fake.phone_number(),
            email=fake.company_email(),
            cif=fake.bothify('B########'),
            direccion=fake.address()
        )
        sesion.add(proveedor)
    sesion.commit()
    print(f"Se han creado {n} proveedores.")


def crear_clientes(n=10):
    for _ in range(n):
        cliente = Cliente(
            nombre=fake.first_name(),
            contacto=fake.last_name(),
            telefono=fake.phone_number(),
            email=fake.email(),
            dni=fake.bothify('########X'),
            direccion=fake.address()
        )
        sesion.add(cliente)
    sesion.commit()
    print(f"Se han creado {n} clientes.")


def crear_productos(n=10):
    proveedores = sesion.query(Proveedor).all()

    for _ in range(n):
        proveedor = random.choice(proveedores)
        nombre_producto = fake.word().capitalize() + "_" + str(random.randint(1000, 9999))  # <- nombre único

        producto = Producto(
            nombre=nombre_producto,
            descripcion=fake.sentence(),
            precio=round(random.uniform(5.0, 150.0), 2),
            stock=random.randint(10, 100),
            proveedor_id=proveedor.id
        )
        sesion.add(producto)
    sesion.commit()
    print(f"Se han creado {n} productos.")



def crear_ventas(n=50):
    clientes = sesion.query(Cliente).all()
    productos = sesion.query(Producto).all()

    for _ in range(n):
        cliente = random.choice(clientes)
        fecha = fake.date_between(start_date='-6M', end_date='today')
        descuento = random.choice([0, 5, 10, 15])

        nueva_venta = Venta(
            cliente_id=cliente.id,
            fecha=fecha,
            total=0,
            descuento=descuento,
            total_final=0,
            pagado=random.choice([True, False])
        )
        sesion.add(nueva_venta)
        sesion.commit()

        total = 0
        for _ in range(random.randint(1, 4)):
            producto = random.choice(productos)
            cantidad = random.randint(1, 5)

            if producto.stock < cantidad:
                continue

            subtotal = cantidad * producto.precio
            detalle = DetalleVenta(
                venta_id=nueva_venta.id,
                producto_id=producto.id,
                cantidad=cantidad,
                precio_unitario=producto.precio,
                subtotal=subtotal
            )
            sesion.add(detalle)

            producto.stock -= cantidad
            total += subtotal

        total_final = total * (1 - Decimal(descuento) / 100)
        nueva_venta.total = total
        nueva_venta.total_final = total_final
        sesion.commit()
    print(f"Se han creado {n} ventas con detalles.")


def crear_compras(n=30):
    productos = sesion.query(Producto).all()
    proveedores = sesion.query(Proveedor).all()

    for _ in range(n):
        producto = random.choice(productos)
        proveedor = random.choice(proveedores)
        cantidad = random.randint(5, 20)
        precio_unitario = round(random.uniform(3.0, 50.0), 2)
        total = cantidad * precio_unitario
        fecha = fake.date_between(start_date='-6M', end_date='today')

        nueva_compra = Compra(
            producto_id=producto.id,
            proveedor_id=proveedor.id,
            precio=precio_unitario,
            cantidad=cantidad,
            total=total,
            fecha=fecha
        )
        sesion.add(nueva_compra)
        producto.stock += cantidad  # Aumenta el stock al comprar

    sesion.commit()
    print(f"Se han creado {n} compras.")


if __name__ == '__main__':
    crear_proveedores(5)
    crear_clientes(15)
    crear_productos(10)
    crear_ventas(50)
    crear_compras(30)
    print("✅ Datos de prueba generados correctamente.")

# python generar_datos_prueba.py
