from flask import Blueprint

game_bp = Blueprint('events', __name__, url_prefix='/events')

from . import routes  # Importa las rutas para registrarlas