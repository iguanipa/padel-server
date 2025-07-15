from flask import jsonify, request
from . import game_bp
from .admin_manager import AdminManager

@game_bp.route('/cancha/<int:court_id>/reset', methods=['POST'])
def reset_court_data(court_id):
    confirm = request.args.get('confirm', 'false').lower() == 'true'
    manager = AdminManager(court_id)
    result = manager.reset_court(confirm=confirm)
    
    # Convertir a respuesta HTTP apropiada
    status_code = 200 if result['status'] == 'success' else \
                  202 if result['status'] == 'confirmation_required' else \
                  500
    return jsonify(result), status_code

@game_bp.route('/cancha/<int:court_id>/status', methods=['GET'])
def get_court_status(court_id):
    result = AdminManager.get_court_status(court_id)
    status_code = 200 if result['status'] == 'success' else 500
    return jsonify(result), status_code

# game/admin_routes.py
@game_bp.route('/cancha/<int:court_id>/initialize', methods=['POST'])
def initialize_court(court_id):
    # Datos por defecto
    DEFAULT_TEAMS = {
        'azul': {'name': 'Azul', 'players': ['Jugador Azul 1', 'Jugador Azul 2']},
        'rojo': {'name': 'Rojo', 'players': ['Jugador Rojo 1', 'Jugador Rojo 2']}
    }

    try:
        data = request.get_json(silent=True) or {}
        
        # Usar datos proporcionados o los por defecto
        team_a_data = data.get('team_a', DEFAULT_TEAMS['azul'])
        team_b_data = data.get('team_b', DEFAULT_TEAMS['rojo'])

        # Validar estructura
        for team_data in [team_a_data, team_b_data]:
            if 'name' not in team_data:
                team_data['name'] = DEFAULT_TEAMS['azul']['name']
            if 'players' not in team_data or len(team_data['players']) != 2:
                team_data['players'] = DEFAULT_TEAMS['azul']['players'][:2]

        manager = AdminManager(court_id)
        result = manager.initialize_court(team_a_data, team_b_data)
        
        status_code = 200 if result['status'] in ['success', 'partial_success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'court_id': court_id
        }), 500