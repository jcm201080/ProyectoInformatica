import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Blueprint, render_template
from sqlalchemy import func, extract
from db import Compra,  DetalleVenta,sesion, Producto, Proveedor, login_required, rol_requerido



graficas_py_bp = Blueprint('graficas_py', __name__)

@graficas_py_bp.route("/graficas/python/ventas")
def graficas_ventas_python():
    os.makedirs("static/graficas", exist_ok=True)

    # 1. Ventas por producto
    datos_ventas = sesion.query(Producto.nombre, func.sum(DetalleVenta.cantidad)) \
        .join(DetalleVenta.producto) \
        .group_by(Producto.id).all()

    if datos_ventas:
        nombres = [nombre for nombre, _ in datos_ventas]
        cantidades = [cantidad for _, cantidad in datos_ventas]
        colores = ['#FF5733', '#33FF57', '#3357FF', '#FFFF33', '#FF33A1', '#800080']

        plt.figure(figsize=(10, 6))
        plt.bar(nombres, cantidades, color=colores[:len(nombres)])
        plt.title("Ventas por Producto")
        plt.xlabel("Producto")
        plt.ylabel("Cantidad Vendida")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/graficas/ventas.png")
        plt.close()

    # 2. Compras por proveedor
    datos_prov = (
        sesion.query(Proveedor.nombre, func.sum(Compra.total))
        .join(Compra, Proveedor.id == Compra.proveedor_id)
        .group_by(Proveedor.nombre)
        .all()
    )

    if datos_prov:
        nombres = [d[0] for d in datos_prov]
        totales = [float(d[1]) for d in datos_prov]

        plt.figure(figsize=(10, 6))
        plt.bar(nombres, totales)
        plt.title("Total de Compras por Proveedor")
        plt.ylabel("Total (€)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/graficas/compras_por_proveedor.png")
        plt.close()

    # 3. Compras por mes
    datos_mes = (
        sesion.query(extract('month', Compra.fecha), func.sum(Compra.total))
        .group_by(extract('month', Compra.fecha))
        .order_by(extract('month', Compra.fecha))
        .all()
    )

    if datos_mes:
        meses = [int(d[0]) for d in datos_mes]
        totales = [float(d[1]) for d in datos_mes]
        etiquetas = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                     'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
        etiquetas_m = [etiquetas[m - 1] for m in meses]

        plt.figure(figsize=(10, 6))
        plt.plot(etiquetas_m, totales, marker='o', color='green')
        plt.title("Compras por Mes")
        plt.ylabel("Total (€)")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig("static/graficas/compras_por_mes.png")
        plt.close()

    # 4. Comparativa Compras vs Ventas por Producto
    datos_ventas = (
        sesion.query(Producto.id, Producto.nombre, func.sum(DetalleVenta.cantidad))
        .join(DetalleVenta, Producto.id == DetalleVenta.producto_id)
        .group_by(Producto.id)
        .all()
    )

    datos_compras = (
        sesion.query(Producto.id, func.sum(Compra.cantidad))
        .join(Compra, Producto.id == Compra.producto_id)
        .group_by(Producto.id)
        .all()
    )

    vendidos_dict = {id_: cantidad for id_, _, cantidad in datos_ventas}
    comprados_dict = {id_: cantidad for id_, cantidad in datos_compras}

    productos = list(set(vendidos_dict.keys()) | set(comprados_dict.keys()))
    productos.sort()

    nombres = [sesion.query(Producto.nombre).filter_by(id=id_).scalar() for id_ in productos]
    vendidos = [vendidos_dict.get(id_, 0) for id_ in productos]
    comprados = [comprados_dict.get(id_, 0) for id_ in productos]

    x = range(len(nombres))
    plt.figure(figsize=(12, 6))
    plt.bar(x, comprados, width=0.4, label='Comprados', align='center')
    plt.bar([i + 0.4 for i in x], vendidos, width=0.4, label='Vendidos', align='center')
    plt.xticks([i + 0.2 for i in x], nombres, rotation=45)
    plt.ylabel("Cantidad")
    plt.title("Comparativa Compras vs Ventas por Producto")
    plt.legend()
    plt.tight_layout()
    plt.savefig("static/graficas/comparativa_productos.png")
    plt.close()


    return render_template("graficas/python/ventas.html")

