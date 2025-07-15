# game/admin_manager.py
from .models import db, Team, Player, Point, Court
from datetime import datetime

class AdminManagerSetting:
    def _get_courts():
        result =  Court.query.all()
        data = [{
        "id": cancha.id,
        "name": cancha.name,
        "code": cancha.code
        } for cancha in result]
        return data

class AdminManager:
    def __init__(self, court_id=None):
        self.court_id = court_id

    def reset_court(self, confirm=False):
        """
        Resetea todos los datos de una cancha específica
        :param confirm: Requerido para ejecutar la acción
        :return: dict con resultados
        """
        if not self.court_id:
            return {'status': 'error', 'message': 'Court ID not specified'}

        try:
            if not confirm:
                return {
                    'status': 'confirmation_required',
                    'message': 'Confirmación requerida para resetear',
                    'court_id': self.court_id
                }

            # Eliminar en orden adecuado
            deleted_data = {
                'points': 0,
                'players': 0,
                'teams': 0
            }

            # 1. Eliminar puntos
            deleted_data['points'] = Point.query.filter_by(court_id=self.court_id).delete()
            
            # 2. Obtener equipos y eliminar jugadores
            teams = Team.query.filter_by(court_id=self.court_id).all()
            team_ids = [team.id for team in teams]
            
            if team_ids:
                deleted_data['players'] = Player.query.filter(Player.team_id.in_(team_ids)).delete()
            
            # 3. Eliminar equipos
            deleted_data['teams'] = Team.query.filter_by(court_id=self.court_id).delete()
            
            db.session.commit()
            
            return {
                'status': 'success',
                'message': f'Cancha {self.court_id} reseteada',
                'deleted': deleted_data
            }

        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': str(e),
                'court_id': self.court_id
            }

    def create_team(self, team_name, color,players=None):
        """
        Crea un nuevo equipo para la cancha
        :param team_name: Nombre del equipo (ej: "Azul")
        :param players: Lista de nombres de jugadores
        :return: dict con resultado
        """
        if not self.court_id:
            return {'status': 'error', 'message': 'Court ID not specified'}

        try:
            # Crear equipo
            new_team = Team(
                name=team_name,
                color=color,
                court_id=self.court_id
            )
            db.session.add(new_team)
            db.session.flush()  # Para obtener el ID
            
            # Crear jugadores si se especifican
            created_players = []
            if players:
                for player_name in players:
                    player = Player(
                        name=player_name,
                        team_id=new_team.id
                    )
                    db.session.add(player)
                    created_players.append(player_name)
            
            db.session.commit()
            
            return {
                'status': 'success',
                'team_id': new_team.id,
                'team_name': team_name,
                'color': color,
                'players': created_players
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': str(e)
            }

    @staticmethod
    def get_court_status(court_id):
        """
        Obtiene el estado administrativo de una cancha
        :param court_id: ID de la cancha
        :return: dict con información
        """
        try:
            teams = Team.query.filter_by(court_id=court_id).all()
            
            court_data = {
                'court_id': court_id,
                'teams': [],
                'total_players': 0,
                'total_points': Point.query.filter_by(court_id=court_id).count()
            }
            
            for team in teams:
                players = Player.query.filter_by(team_id=team.id).all()
                court_data['teams'].append({
                    'id': team.id,
                    'name': team.name,
                    'players': [p.name for p in players],
                    'player_count': len(players)
                })
                court_data['total_players'] += len(players)
            
            return {
                'status': 'success',
                'data': court_data
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e)
            }
    # game/admin_manager.py
    def initialize_court(self, team_a_data, team_b_data):
        """
        Crea ambos equipos con sus jugadores para una cancha
        :param team_a_data: {'name': str, 'players': [str, str]}
        :param team_b_data: {'name': str, 'players': [str, str]}
        :return: dict con resultados
        """
        if not self.court_id:
            return {'status': 'error', 'message': 'Court ID not specified'}

        try:
            results = {
                'court_id': self.court_id,
                'teams': []
            }

            # Crear equipo A
            team_a_result = self.create_team(
                team_name=team_a_data['name'],
                color=team_a_data['color'],
                players=team_a_data.get('players', [])
            )
            results['teams'].append(team_a_result)

            # Crear equipo B
            team_b_result = self.create_team(
                team_name=team_b_data['name'],
                color=team_b_data['color'],
                players=team_b_data.get('players', [])
            )
            results['teams'].append(team_b_result)

            # Verificar que todo se creó correctamente
            if all(t['status'] == 'success' for t in results['teams']):
                results['status'] = 'success'
                results['message'] = 'Court initialized successfully'
            else:
                results['status'] = 'partial_success'
                results['message'] = 'Some teams might not have been created'

            return results

        except Exception as e:
            db.session.rollback()
            return {
                'status': 'error',
                'message': str(e),
                'court_id': self.court_id
            }
    
    