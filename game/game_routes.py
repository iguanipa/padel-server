from . import game_bp  # Importar el blueprint local
from flask import jsonify, request, render_template, json
from .pointservice import PadelScoreManager
from .models import db, Player
from .sockets import  emitir_actualizacion  # Importa las utilidades


@game_bp.route("/cancha/<int:cancha_id>")
def marcador_por_cancha(cancha_id):
    try:
        # Crear el manager que cargará el estado automáticamente
        manager = PadelScoreManager(cancha_id)
        
        # Obtener el estado actual (incluye equipos y jugadores)
        estado = manager._get_full_state()
            
        return render_template(
            "score.html",
            cancha_id=cancha_id,
            estado_inicial=json.dumps(estado)  # Enviamos todo el estado inicial
        )
        
    except ValueError as e:
        # Si hay error (ej: cancha no existe), mostrar pantalla de error
        print(f"Error cargando cancha {cancha_id}: {str(e)}")
    except Exception as e:
        print(f"Error inesperado: {str(e)}")


@game_bp.route("/cancha/<int:cancha_id>/punto", methods=["POST"])
def manejar_punto(cancha_id):
    data = request.get_json()
    
    # Cambiamos la validación para usar 'color' en lugar de 'team_id'
    if not data or 'color' not in data or 'signal' not in data:
        return jsonify({"error": "Se requieren color (azul/rojo) y signal (1/-1)"}), 400
    
    try:
        manager = PadelScoreManager(cancha_id)
        
        # Validar señal
        signal = data['signal']
        if signal not in [-1, 1]:
            return jsonify({"error": "Signal debe ser 1 (sumar) o -1 (restar)"}), 400
        
        # Validar color
        color = data['color'].lower()
        if color not in ['azul', 'rojo']:
            return jsonify({"error": "Color debe ser 'azul' o 'rojo'"}), 400
        
        # Obtener team_id basado en el color
        team_id = manager.blue_team.id if color == 'azul' else manager.red_team.id
        
        # Procesar señal
        estado = manager.procesar_senal(
            team_id=team_id,
            signal=signal
        )
        
        emitir_actualizacion(cancha_id, estado)
        
        return jsonify({
            "success": True,
            "state": estado,
            "team_id": team_id  # Para referencia
        }), 200
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": "Error interno del servidor"}), 500