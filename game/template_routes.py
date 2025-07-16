from . import game_bp  # Importar el blueprint local
from flask import jsonify, request, render_template, json
from .pointservice import PadelScoreManager
from .models import db, Player
from .sockets import  emitir_actualizacion  # Importa las utilidades


@game_bp.route("/cancha/<int:cancha_id>/template")
def cancha_template(cancha_id):
    return render_template(
        "score.html",
        cancha_id=cancha_id,
    )
 