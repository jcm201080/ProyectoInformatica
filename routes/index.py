from flask import Blueprint

index_bp = Blueprint('index', __name__)

@index_bp.route('/')
def index():
    index = sesion.query(Cliente).all()
    return render_template('index.html', index=index)