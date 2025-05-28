from flask import Blueprint, render_template, jsonify
from db import sesion, Producto, Proveedor, login_required, rol_requerido

from sqlalchemy import func
import matplotlib.pyplot as plt
import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


graficas_bp = Blueprint('graficas', __name__)

# =========================
# GRÁFICAS CON JAVASCRIPT
# =========================

@graficas_bp.route('/graficas/js')
def graficas():
    return render_template('graficas/js/graficas.html')

@graficas_bp.route('/graficas/stock_productos')
def stock_productos():
    datos = sesion.query(Producto.nombre, Producto.stock).all()
    nombres = [nombre for nombre, _ in datos]
    stocks = [stock for _, stock in datos]
    return jsonify({"nombres": nombres, "stocks": stocks})

@graficas_bp.route('/graficas/ventas_por_cliente')
def ventas_por_cliente():
    from db import Cliente, Venta
    datos = sesion.query(
        Cliente.nombre,
        func.sum(Venta.total_final)
    ).join(Venta).group_by(Cliente.nombre).all()
    nombres = [cliente for cliente, _ in datos]
    totales = [float(total) for _, total in datos]
    return jsonify({"clientes": nombres, "totales": totales})

@graficas_bp.route('/graficas/ingresos_por_mes')
def ingresos_por_mes():
    from db import Venta
    datos = sesion.query(
        func.substr(Venta.fecha, 6, 2).label("mes"),
        func.sum(Venta.total_final).label("ingresos")
    ).group_by(func.substr(Venta.fecha, 6, 2)).order_by("mes").all()
    meses = [mes for mes, _ in datos]
    ingresos = [float(ingreso) for _, ingreso in datos]
    return jsonify({"meses": meses, "ingresos": ingresos})

@graficas_bp.route('/graficas/comparativa_proveedores')
@rol_requerido('admin')
def comparativa_proveedores():
    from db import Proveedor, DetalleVenta
    proveedores = sesion.query(Producto.proveedor).distinct().all()
    nombres = []
    compras = []
    ventas = []

    for proveedor in proveedores:
        productos = sesion.query(Producto).filter_by(proveedor_id=proveedor.id).all()
        ids_productos = [p.id for p in productos]
        total_comprado = sum([p.cantidad_total or 0 for p in productos])
        total_vendido = sesion.query(func.sum(DetalleVenta.cantidad)).filter(
            DetalleVenta.producto_id.in_(ids_productos)
        ).scalar() or 0

        nombres.append(proveedor.nombre)
        compras.append(total_comprado)
        ventas.append(total_vendido)

    return jsonify({"proveedores": nombres, "compras": compras, "ventas": ventas})



#Graficas ventas por ubicación
@graficas_bp.route("/graficas/python")
@rol_requerido('admin')
def generar_grafico_ventas_por_ubicacion():
    from sqlalchemy import func
    from db import sesion, Ubicacion, Venta, DetalleVenta
    import os
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    print("🟦 Generando imagen de ventas por ubicación...")

    # Crear carpeta si no existe
    os.makedirs("static/graficas", exist_ok=True)

    # Consulta de datos
    datos = (
        sesion.query(Ubicacion.nombre, func.sum(DetalleVenta.cantidad))
        .join(Venta, Ubicacion.id == Venta.ubicacion_id)
        .join(DetalleVenta, Venta.id == DetalleVenta.venta_id)
        .group_by(Ubicacion.nombre)
        .all()
    )

    # Generar gráfica si hay datos
    if datos:
        ubicaciones = [d[0] for d in datos]
        cantidades = [int(d[1]) for d in datos]

        plt.figure(figsize=(10, 6))
        plt.bar(ubicaciones, cantidades, color='#FF6F61')  # Color coral atractivo
        plt.title("Comparativa de Ventas por Tienda")
        plt.xlabel("Ubicación")
        plt.ylabel("Cantidad Vendida")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("static/graficas/ventas_por_ubicacion.png")
        plt.close()
        print("✅ Gráfica generada correctamente.")
    else:
        print("⚠️ No hay datos de ventas por ubicación.")

    return render_template("graficas/python/graficas_python.html")
