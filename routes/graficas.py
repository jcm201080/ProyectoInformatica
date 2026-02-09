from flask import Blueprint, render_template, jsonify, request
from sqlalchemy import func
from db import (
    Session,
    Producto,
    Proveedor,
    Cliente,
    Venta,
    DetalleVenta,
    login_required
)

graficas_bp = Blueprint('graficas', __name__)

# =========================
# GRÁFICAS CON JAVASCRIPT
# =========================

@graficas_bp.route('/graficas/js')
@login_required
def graficas():
    return render_template('graficas/js/graficas.html')


# 📊 Stock actual por producto
@graficas_bp.route('/graficas/stock_productos')
@login_required
def stock_productos():
    sesion = Session()
    try:
        datos = sesion.query(Producto.nombre, Producto.stock).all()
        return jsonify({
            "nombres": [n for n, _ in datos],
            "stocks": [s for _, s in datos]
        })
    finally:
        sesion.close()


# 🧾 Ventas por cliente
@graficas_bp.route('/graficas/ventas_por_cliente')
@login_required
def ventas_por_cliente():
    sesion = Session()
    try:
        datos = (
            sesion.query(
                Cliente.nombre,
                func.sum(Venta.total_final)
            )
            .join(Venta)
            .group_by(Cliente.nombre)
            .all()
        )

        return jsonify({
            "clientes": [c for c, _ in datos],
            "totales": [float(t) for _, t in datos]
        })
    finally:
        sesion.close()


# 💰 Ingresos por mes
@graficas_bp.route('/graficas/ingresos_por_mes')
@login_required
def ingresos_por_mes():
    sesion = Session()
    try:
        datos = (
            sesion.query(
                func.substr(Venta.fecha, 6, 2).label("mes"),
                func.sum(Venta.total_final).label("ingresos")
            )
            .group_by("mes")
            .order_by("mes")
            .all()
        )

        return jsonify({
            "meses": [m for m, _ in datos],
            "ingresos": [float(i) for _, i in datos]
        })
    finally:
        sesion.close()


# 📆 Ventas por producto en un mes dado
@graficas_bp.route("/api/ventas_por_mes")
@login_required
def api_ventas_por_mes():
    anio = request.args.get("anio")
    mes = request.args.get("mes")

    if not anio or not mes:
        return jsonify({"error": "Debes proporcionar año y mes"}), 400

    sesion = Session()
    try:
        detalles = (
            sesion.query(
                Producto.nombre.label("producto"),
                func.sum(DetalleVenta.cantidad).label("cantidad")
            )
            .join(DetalleVenta)
            .join(Venta)
            .filter(
                func.extract('year', Venta.fecha) == int(anio),
                func.extract('month', Venta.fecha) == int(mes)
            )
            .group_by(Producto.nombre)
            .all()
        )

        return jsonify({
            "productos": [p for p, _ in detalles],
            "cantidades": [int(c) for _, c in detalles]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        sesion.close()
