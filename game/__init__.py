from flask import Blueprint

game_bp = Blueprint(
    "game",
    __name__,
    template_folder="templates",  # 👈 Esto le dice dónde buscar los HTML
    static_folder="static",        # Opcional si tienes CSS o JS
    url_prefix='/game'
)

from . import routes  # Importa las rutas para registrarlas