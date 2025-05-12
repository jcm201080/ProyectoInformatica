from flask import Blueprint, render_template, jsonify
from db import sesion, Producto, Proveedor, login_required, rol_requerido

from sqlalchemy import func
import matplotlib.pyplot as plt
import os

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




