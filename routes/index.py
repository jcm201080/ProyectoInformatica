from flask import Blueprint, render_template
from db import Session, Cliente

index_bp = Blueprint('index', __name__)

# 🏠 Página principal
@index_bp.route('/')
def index():
    sesion = Session()
    try:
        clientes = sesion.query(Cliente).all()
        return render_template('index.html', clientes=clientes)
    finally:
        sesion.close()
