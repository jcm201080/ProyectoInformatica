from flask import Blueprint, render_template, jsonify, request
from db import sesion, Producto, Proveedor, Cliente, Venta, DetalleVenta, login_required, rol_requerido
from sqlalchemy import func
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

# 📊 Stock actual por producto
@graficas_bp.route('/graficas/stock_productos')
def stock_productos():
    datos = sesion.query(Producto.nombre, Producto.stock).all()
    nombres = [nombre for nombre, _ in datos]
    stocks = [stock for _, stock in datos]
    return jsonify({"nombres": nombres, "stocks": stocks})

# 🧾 Ventas por cliente
@graficas_bp.route('/graficas/ventas_por_cliente')
def ventas_por_cliente():
    datos = sesion.query(
        Cliente.nombre,
        func.sum(Venta.total_final)
    ).join(Venta).group_by(Cliente.nombre).all()
    nombres = [cliente for cliente, _ in datos]
    totales = [float(total) for _, total in datos]
    return jsonify({"clientes": nombres, "totales": totales})

# 💰 Ingresos por mes
@graficas_bp.route('/graficas/ingresos_por_mes')
def ingresos_por_mes():
    datos = sesion.query(
        func.substr(Venta.fecha, 6, 2).label("mes"),
        func.sum(Venta.total_final).label("ingresos")
    ).group_by(func.substr(Venta.fecha, 6, 2)).order_by("mes").all()
    meses = [mes for mes, _ in datos]
    ingresos = [float(ingreso) for _, ingreso in datos]
    return jsonify({"meses": meses, "ingresos": ingresos})



# 📆 Ventas por producto en un mes dado
@graficas_bp.route("/api/ventas_por_mes")
def api_ventas_por_mes():
    anio = request.args.get("anio")
    mes = request.args.get("mes")

    if not anio or not mes:
        return jsonify({"error": "Debes proporcionar año y mes"}), 400

    try:
        # Consulta a la base de datos filtrando por año y mes
        detalles = (
            sesion.query(
                Producto.nombre.label("producto_nombre"),
                func.sum(DetalleVenta.cantidad).label("total_cantidad")
            )
            .join(DetalleVenta, Producto.id == DetalleVenta.producto_id)
            .join(Venta, DetalleVenta.venta_id == Venta.id)
            .filter(
                func.extract('year', Venta.fecha) == int(anio),
                func.extract('month', Venta.fecha) == int(mes)
            )
            .group_by(Producto.nombre)
            .all()
        )

        productos = [p for p, _ in detalles]
        cantidades = [c for _, c in detalles]

        return jsonify({
            "productos": productos,
            "cantidades": cantidades
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500