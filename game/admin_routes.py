from . import game_bp  # Importar el blueprint local
from flask import jsonify, request, render_template
from .pointservice import PadelScoreManager
from .models import db, Player
from .sockets import  emitir_actualizacion  # Importa las utilidades

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
