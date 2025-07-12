from flask import Blueprint
import logging

logger = logging.getLogger("game")
logger.setLevel(logging.INFO)  # Puedes usar DEBUG para más detalle

game_bp = Blueprint('game', __name__, url_prefix='/game')

from . import routes  # Importa las rutas para registrarlas

if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    