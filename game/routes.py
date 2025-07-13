from . import game_bp
from flask import render_template
from flask import jsonify
from .services import get_game_status

@game_bp.route('/test')
def status():
    return jsonify({"test":1})

@game_bp.route("/cancha/<int:cancha_id>")
def marcador_por_cancha(cancha_id):
    estado =1
    """ from .services import get_game_status
    estado = get_game_status(cancha_id)

    if estado is None:
        return render_template("error.html", mensaje="Cancha no encontrada"), 404 """

    return render_template("score.html", estado=estado)