from . import game_bp  # Importar el blueprint local
from flask import jsonify, request, render_template
from .pointservice import PadelScoreManager, PointAction
from .models import db, Player
from .sockets import  emitir_actualizacion  # Importa las utilidades


@game_bp.route('/test')
def status():
    return jsonify({"test": 1})

@game_bp.route("/cancha/<int:cancha_id>")
def marcador_por_cancha(cancha_id):
    return render_template("score.html")


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


@game_bp.route("/cancha/<int:cancha_id>/punto", methods=["POST"])
def manejar_punto(cancha_id):
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "Datos requeridos"}), 400
    
    try:
        manager = PadelScoreManager(cancha_id)
        
        # Validación y conversión directa de signal a PointAction
        if 'signal' not in data or data['signal'] not in [-1, 1]:
            return jsonify({"error": "Signal debe ser 1 (sumar) o -1 (restar)"}), 400
        
        action = PointAction(data['signal'])  # Conversión directa
        
        if action == PointAction.UNDO:
            team_id = None
        else:
            if 'team_id' not in data:
                return jsonify({"error": "team_id es requerido"}), 400
            team_id = data['team_id']
        
        new_state = manager.process_action(team_id, action)
        emitir_actualizacion(cancha_id, new_state)
        
        return jsonify({
            "success": True,
            "state": new_state
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500