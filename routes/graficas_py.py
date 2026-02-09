import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Blueprint, render_template
from sqlalchemy import func, extract
from datetime import datetime, timedelta

from db import (
    Session,
    Venta,
    Compra,
    DetalleVenta,
    Producto,
    Proveedor,
    Cliente,
    Ubicacion,
    login_required
)

graficas_py_bp = Blueprint('graficas_py', __name__)


# 🔧 Función auxiliar: ventas por ubicación
def generar_grafico_ventas_por_ubicacion(sesion):
    os.makedirs("static/graficas", exist_ok=True)

    datos = (
        sesion.query(Ubicacion.nombre, func.sum(DetalleVenta.cantidad))
        .join(Venta, Ubicacion.id == Venta.ubicacion_id)
        .join(DetalleVenta, Venta.id == DetalleVenta.venta_id)
        .group_by(Ubicacion.nombre)
        .all()
    )

    if not datos:
        return

    ubicaciones = [d[0] for d in datos]
    cantidades = [int(d[1]) for d in datos]

    plt.figure(figsize=(10, 6))
    plt.bar(ubicaciones, cantidades)
    plt.title("Comparativa de Ventas por Tienda")
    plt.xlabel("Ubicación")
    plt.ylabel("Cantidad Vendida")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig("static/graficas/ventas_por_ubicacion.png")
    plt.close()


# 📊 Página principal de gráficas
@graficas_py_bp.route("/graficas/python")
@login_required
def graficas_python():
    sesion = Session()
    try:
        os.makedirs("static/graficas", exist_ok=True)

        # 1️⃣ Ventas por producto
        datos_ventas = (
            sesion.query(Producto.nombre, func.sum(DetalleVenta.cantidad))
            .join(DetalleVenta, Producto.id == DetalleVenta.producto_id)
            .group_by(Producto.id)
            .all()
        )

        if datos_ventas:
            nombres = [n for n, _ in datos_ventas]
            cantidades = [int(c) for _, c in datos_ventas]

            plt.figure(figsize=(10, 6))
            plt.bar(nombres, cantidades)
            plt.title("Ventas por Producto")
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig("static/graficas/ventas.png")
            plt.close()

        # 2️⃣ Compras por proveedor
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
            plt.xticks(rotation=45)
            plt.tight_layout()
            plt.savefig("static/graficas/compras_por_proveedor.png")
            plt.close()

        # 3️⃣ Compras por mes
        datos_mes = (
            sesion.query(extract('month', Compra.fecha), func.sum(Compra.total))
            .group_by(extract('month', Compra.fecha))
            .order_by(extract('month', Compra.fecha))
            .all()
        )

        if datos_mes:
            meses = [int(d[0]) for d in datos_mes]
            totales = [float(d[1]) for d in datos_mes]
            etiquetas = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
            etiquetas_m = [etiquetas[m-1] for m in meses]

            plt.figure(figsize=(10, 6))
            plt.plot(etiquetas_m, totales, marker='o')
            plt.title("Compras por Mes")
            plt.grid(True)
            plt.tight_layout()
            plt.savefig("static/graficas/compras_por_mes.png")
            plt.close()

        # 4️⃣ Comparativa compras vs ventas
        ventas = (
            sesion.query(Producto.id, func.sum(DetalleVenta.cantidad))
            .join(DetalleVenta)
            .group_by(Producto.id)
            .all()
        )

        compras = (
            sesion.query(Producto.id, func.sum(Compra.cantidad))
            .join(Compra)
            .group_by(Producto.id)
            .all()
        )

        v_dict = dict(ventas)
        c_dict = dict(compras)

        ids = sorted(set(v_dict) | set(c_dict))
        nombres = [sesion.get(Producto, i).nombre for i in ids]
        vendidos = [v_dict.get(i, 0) for i in ids]
        comprados = [c_dict.get(i, 0) for i in ids]

        x = range(len(nombres))
        plt.figure(figsize=(12, 6))
        plt.bar(x, comprados, width=0.4, label='Comprados')
        plt.bar([i+0.4 for i in x], vendidos, width=0.4, label='Vendidos')
        plt.xticks([i+0.2 for i in x], nombres, rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.savefig("static/graficas/comparativa_productos.png")
        plt.close()

        # 5️⃣ Ventas por ubicación
        generar_grafico_ventas_por_ubicacion(sesion)

        # 6️⃣ Ventas mensuales por tienda
        desde = datetime.today() - timedelta(days=365)
        ubicaciones = ["Oficina1 (Sevilla)", "Oficina2 (Madrid)", "Oficina3 (Valencia)"]

        resultados = (
            sesion.query(
                Ubicacion.nombre,
                extract("month", Venta.fecha),
                func.sum(Venta.total_final)
            )
            .join(Venta)
            .filter(Venta.fecha >= desde, Ubicacion.nombre.in_(ubicaciones))
            .group_by(Ubicacion.nombre, extract("month", Venta.fecha))
            .all()
        )

        datos = {u: [0]*12 for u in ubicaciones}
        for u, mes, total in resultados:
            datos[u][int(mes)-1] = float(total)

        plt.figure(figsize=(12, 6))
        for u, valores in datos.items():
            plt.plot(range(1,13), valores, marker='o', label=u)

        plt.xticks(range(1,13), ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'])
        plt.legend()
        plt.tight_layout()
        plt.savefig("static/graficas/ventas_ubicaciones_mensual.png")
        plt.close()

        return render_template("graficas/python/graficas_python.html")

    finally:
        sesion.close()
