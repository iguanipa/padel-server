from flask import Blueprint

game_bp = Blueprint('game', __name__, url_prefix='/game')

from . import routes  # Importa las rutas para registrarlas