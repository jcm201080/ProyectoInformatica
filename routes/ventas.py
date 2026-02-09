from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from sqlalchemy import func
from decimal import Decimal
from db import (
    Session, Venta, DetalleVenta, Cliente,
    Producto, Ubicacion, StockPorUbicacion,
    login_required, rol_requerido
)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io
from routes.graficas_py import generar_grafico_ventas_por_ubicacion

ventas_bp = Blueprint("ventas", __name__)

# =====================================================
# 📋 Listado de ventas
# =====================================================
@ventas_bp.route("/ventas")
@login_required
def ventas():
    sesion = Session()
    try:
        cliente = request.args.get("cliente")
        pagado = request.args.get("pagado")
        pagina = int(request.args.get("pagina", 1))
        orden = request.args.get("orden", "id")
        direccion = request.args.get("direccion", "desc")
        por_pagina = 30

        query = sesion.query(Venta).join(Cliente)

        if cliente:
            query = query.filter(Cliente.nombre.ilike(f"%{cliente}%"))
        if pagado in ("0", "1"):
            query = query.filter(Venta.pagado == bool(int(pagado)))

        def ordenar(campo):
            return campo.desc() if direccion == "desc" else campo.asc()

        if orden == "cliente":
            query = query.order_by(ordenar(Cliente.nombre))
        elif orden == "fecha":
            query = query.order_by(ordenar(Venta.fecha))
        else:
            query = query.order_by(ordenar(Venta.id))

        total = query.count()
        ventas = query.offset((pagina - 1) * por_pagina).limit(por_pagina).all()

        return render_template(
            "ventas/ventas.html",
            ventas=ventas,
            pagina=pagina,
            hay_anterior=pagina > 1,
            hay_siguiente=(pagina * por_pagina) < total,
            cliente=cliente,
            pagado=pagado,
            orden=orden,
            direccion=direccion
        )
    finally:
        sesion.close()


# =====================================================
# 🆕 Nueva venta
# =====================================================
@ventas_bp.route("/nueva_venta", methods=["GET", "POST"])
@rol_requerido("admin")
def nueva_venta():
    sesion = Session()
    try:
        clientes = sesion.query(Cliente).all()
        productos = sesion.query(Producto).all()
        ubicaciones = sesion.query(Ubicacion).all()

        productos_json = [
            {"id": p.id, "nombre": p.nombre, "precio": float(p.precio)}
            for p in productos
        ]

        if request.method == "POST":
            cliente_id = request.form["cliente_id"]
            ubicacion_id = int(request.form["ubicacion_id"])
            descuento = Decimal(request.form.get("descuento", "0"))
            productos_ids = request.form.getlist("producto_id[]")
            cantidades = request.form.getlist("cantidad[]")

            total = Decimal("0")
            detalles = []

            for pid, cant in zip(productos_ids, cantidades):
                producto = sesion.get(Producto, int(pid))
                cantidad = int(cant)

                stock = sesion.query(StockPorUbicacion).filter_by(
                    producto_id=producto.id,
                    ubicacion_id=ubicacion_id
                ).first()

                if not stock or stock.cantidad < cantidad:
                    flash(f"No hay stock suficiente de {producto.nombre}", "error")
                    return render_template(
                        "ventas/nueva_venta.html",
                        clientes=clientes,
                        productos=productos,
                        ubicaciones=ubicaciones,
                        productos_json=productos_json
                    )

                subtotal = producto.precio * cantidad
                total += subtotal
                detalles.append((producto, cantidad, subtotal))

            total_final = total * (1 - descuento / 100)

            venta = Venta(
                cliente_id=cliente_id,
                ubicacion_id=ubicacion_id,
                total=total,
                descuento=descuento,
                total_final=total_final
            )
            sesion.add(venta)
            sesion.flush()

            for producto, cantidad, subtotal in detalles:
                sesion.add(DetalleVenta(
                    venta_id=venta.id,
                    producto_id=producto.id,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal
                ))

                stock = sesion.query(StockPorUbicacion).filter_by(
                    producto_id=producto.id,
                    ubicacion_id=ubicacion_id
                ).first()
                stock.cantidad -= cantidad

            sesion.commit()
            generar_grafico_ventas_por_ubicacion()

            flash("Venta registrada correctamente ✅", "success")
            return redirect(url_for("ventas.ventas"))

        return render_template(
            "ventas/nueva_venta.html",
            clientes=clientes,
            productos=productos,
            ubicaciones=ubicaciones,
            productos_json=productos_json
        )
    finally:
        sesion.close()


# =====================================================
# 🔎 Detalle de venta
# =====================================================
@ventas_bp.route("/venta_detalle/<int:venta_id>")
@login_required
def ver_detalle_venta(venta_id):
    sesion = Session()
    try:
        venta = sesion.get(Venta, venta_id)
        if not venta:
            return "Venta no encontrada", 404

        return render_template(
            "ventas/detalle_venta.html",
            venta=venta,
            productos=venta.detalles,
            descuento=venta.descuento,
            total_final=venta.total_final
        )
    finally:
        sesion.close()


# =====================================================
# 🗑️ Eliminar venta
# =====================================================
@ventas_bp.route("/ventas/eliminar/<int:venta_id>", methods=["POST"])
@rol_requerido("admin")
def eliminar_venta(venta_id):
    sesion = Session()
    try:
        venta = sesion.get(Venta, venta_id)
        if not venta:
            flash("Venta no encontrada", "error")
            return redirect(url_for("ventas.ventas"))

        for detalle in venta.detalles:
            sesion.delete(detalle)

        sesion.delete(venta)
        sesion.commit()
        flash("Venta eliminada correctamente 🧨", "success")
    finally:
        sesion.close()

    return redirect(url_for("ventas.ventas"))


# =====================================================
# 📄 Factura PDF
# =====================================================
@ventas_bp.route('/ventas/factura/<int:venta_id>')
@login_required
def descargar_factura(venta_id):
    sesion = Session()
    try:
        venta = sesion.get(Venta, venta_id)
        if not venta:
            return "Factura no encontrada", 404

        detalles = venta.detalles

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elementos = []

        estilos = getSampleStyleSheet()

        # ===============================
        # 🏢 Datos de la empresa
        # ===============================
        empresa = [
            "JCM INFORMÁTICA",
            "Sevilla, 41008",
            "Tel: 635487063",
            "Email: jcm201080@gmail.com"
        ]

        for linea in empresa:
            elementos.append(Paragraph(linea, estilos["Normal"]))

        elementos.append(Spacer(1, 12))

        # ===============================
        # 🧾 Datos de la factura
        # ===============================
        elementos.append(
            Paragraph(f"<strong>Factura Nº:</strong> {venta.id}", estilos["Normal"])
        )
        elementos.append(
            Paragraph(f"<strong>Cliente:</strong> {venta.cliente.nombre}", estilos["Normal"])
        )
        elementos.append(
            Paragraph(
                f"<strong>Fecha:</strong> {venta.fecha.strftime('%d/%m/%Y')}",
                estilos["Normal"]
            )
        )

        elementos.append(Spacer(1, 12))

        # ===============================
        # 📦 Tabla de productos
        # ===============================
        data = [["Producto", "Cantidad", "Precio unitario (€)", "Subtotal (€)"]]

        for detalle in detalles:
            data.append([
                detalle.producto.nombre,
                detalle.cantidad,
                f"{detalle.precio_unitario:.2f}",
                f"{detalle.subtotal:.2f}"
            ])

        # Total final
        data.append(["", "", "TOTAL:", f"{venta.total_final:.2f} €"])

        tabla = Table(data, colWidths=[170, 80, 120, 120])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (1, 1), (-1, -2), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))

        elementos.append(tabla)

        # ===============================
        # 📄 Generar PDF
        # ===============================
        doc.build(elementos)
        buffer.seek(0)

        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"factura_{venta.id}.pdf",
            mimetype="application/pdf"
        )

    finally:
        sesion.close()
