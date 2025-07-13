from flask import Blueprint

game_bp = Blueprint(
    "game",
    __name__,
    template_folder="templates",
    static_folder="static",
    url_prefix='/game'
)

# Importar al final para evitar circularidad
from . import routes