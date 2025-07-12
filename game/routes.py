from . import game_bp
from flask import jsonify
from .services import get_game_status

@game_bp.route('/test')
def status():
    return jsonify({"test":1})