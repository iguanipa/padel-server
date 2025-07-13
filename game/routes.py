from . import game_bp  # Importar el blueprint local
from flask import jsonify, request, render_template
from .services import get_game_status
from .pointservice import MatchStateBuilder
from .models import db, Player
import logging

@game_bp.route('/test')
def status():
    return jsonify({"test": 1})

@game_bp.route("/cancha/<int:cancha_id>")
def marcador_por_cancha(cancha_id):
    estado = get_game_status(cancha_id) or 1
    return render_template("score.html", estado=estado)


@game_bp.route("/cancha/<int:cancha_id>/create-players", methods=["POST"])
def crear_jugadores(cancha_id):
    data = request.get_json()
    print(f"Datos JSON recibidos: {data}")
    
    # Verificar estructura de datos
    if not isinstance(data, dict) or 'data' not in data:
        return jsonify({"error": "Formato inválido, se espera {'data': [...]}"}), 400
    
    try:
        for player_data in data['data']:  # Acceder a la lista dentro de 'data'
            player = Player(
                name=player_data['name'],  # Acceder como diccionario
                team_id=player_data['team_id']
            )
            db.session.add(player)
        
        db.session.commit()  # Mover commit fuera del loop para eficiencia
        return jsonify({"status": "success", "players_created": len(data['data'])})
    
    except KeyError as e:
        db.session.rollback()
        return jsonify({"error": f"Falta campo requerido: {str(e)}"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@game_bp.route("/cancha/<int:cancha_id>/procesar-punto", methods=["POST"])
def procesar_punto(cancha_id):
    data = request.get_json()
    
    if not data or 'team_id' not in data or 'signal' not in data:
        return jsonify({"error": "Datos inválidos"}), 400

    builder = MatchStateBuilder()
    try:
        estado = builder.procesar_senal(
            court_id=cancha_id,
            team_id=data['team_id'],
            signal=data['signal']
        )
        return jsonify(estado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500