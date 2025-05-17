import os
import matplotlib
matplotlib.use('Agg')  # 🔧 Usar backend no interactivo para servidores / Use non-interactive backend
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, redirect, url_for
from sqlalchemy import func, extract
from db import Venta, Compra, DetalleVenta, sesion, Producto, Proveedor, login_required, Cliente

# 🔹 Crear Blueprint para las rutas de gráficas Python / Create Blueprint for Python chart routes
graficas_py_bp = Blueprint('graficas_py', __name__)

# 📊 Ruta: /graficas/python/ventas
# Genera varias gráficas estáticas con matplotlib
# Route: Generates static sales/purchase comparison charts
@graficas_py_bp.route("/graficas/python/graficas_python")
@login_required
def graficas_python():
    os.makedirs("static/graficas", exist_ok=True)

    # 1️⃣ Ventas por producto / Sales per product
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

    # 2️⃣ Compras por proveedor / Purchases per provider
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

    # 3️⃣ Compras por mes / Purchases per month
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

    # 4️⃣ Comparativa Compras vs Ventas / Purchase vs Sales Comparison
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

    ventas_por_cliente()

    return render_template("graficas/python/graficas_python.html")


# 📊 Comparativa mensual (6 meses) / Last 6-month comparison: Sales vs Purchases
@graficas_py_bp.route("/graficas/python/comparativa_mensual")
def comparativa_mensual():
    from datetime import datetime, timedelta
    os.makedirs("static/graficas", exist_ok=True)

    hoy = datetime.today()
    hace_6_meses = hoy - timedelta(days=180)

    # Ventas por mes / Monthly sales
    ventas_mensuales = sesion.query(
        func.strftime("%Y-%m", Venta.fecha),
        func.sum(Venta.total_final)
    ).filter(Venta.fecha >= hace_6_meses) \
     .group_by(func.strftime("%Y-%m", Venta.fecha)) \
     .order_by(func.strftime("%Y-%m", Venta.fecha)).all()

    # Compras por mes / Monthly purchases
    compras_mensuales = sesion.query(
        func.strftime("%Y-%m", Compra.fecha),
        func.sum(Compra.total)
    ).filter(Compra.fecha >= hace_6_meses) \
     .group_by(func.strftime("%Y-%m", Compra.fecha)) \
     .order_by(func.strftime("%Y-%m", Compra.fecha)).all()

    # Unificar meses / Merge months from both queries
    meses = sorted(list(set([v[0] for v in ventas_mensuales] + [c[0] for c in compras_mensuales])))
    ventas_dict = dict(ventas_mensuales)
    compras_dict = dict(compras_mensuales)

    ventas_valores = [float(ventas_dict.get(m, 0)) for m in meses]
    compras_valores = [float(compras_dict.get(m, 0)) for m in meses]

    # Crear la gráfica / Create chart
    plt.figure(figsize=(10, 6))
    plt.plot(meses, ventas_valores, label="Ventas", marker='o')
    plt.plot(meses, compras_valores, label="Compras", marker='s')
    plt.title("Comparativa Ventas vs Compras (6 últimos meses)")
    plt.xlabel("Mes")
    plt.ylabel("Total (€)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("static/graficas/comparativa_mensual.png")
    plt.close()

    return render_template("graficas/python/comparativa_mensual.html")


# 🥧 Gráfica circular: distribución de ventas por cliente / Pie chart: sales distribution by client
@graficas_py_bp.route("/graficas/python/ventas_por_cliente")
def ventas_por_cliente():
    os.makedirs("static/graficas", exist_ok=True)

    datos_clientes = (
        sesion.query(Cliente.nombre, func.sum(Venta.total_final).label("total"))
        .join(Venta, Cliente.id == Venta.cliente_id)
        .group_by(Cliente.nombre)
        .order_by(func.sum(Venta.total_final).desc())
        .limit(20)
        .all()
    )

    if datos_clientes:
        nombres = [c[0] for c in datos_clientes]
        totales = [float(c[1]) for c in datos_clientes]

        plt.figure(figsize=(8, 8))
        plt.pie(totales, labels=nombres, autopct='%1.1f%%', startangle=140)
        plt.title("Distribución de Ventas por Cliente")
        plt.tight_layout()
        plt.savefig("static/graficas/ventas_por_cliente.png")
        plt.close()

        # 📊 Gráfico de barras horizontal
        plt.figure(figsize=(10, 10))
        plt.barh(nombres[::-1], totales[::-1])  # Invertir para mostrar el mayor arriba
        plt.xlabel("Total de ventas (€)")
        plt.title("Ventas por Cliente (Top 20)")
        plt.tight_layout()
        plt.savefig("static/graficas/ventas_por_cliente_barra.png")
        plt.close()


    return redirect(url_for("graficas_py.graficas_python"))
