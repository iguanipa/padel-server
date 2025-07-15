from flask import current_app
from sqlalchemy import desc
from datetime import datetime
from enum import Enum
from game.models import Team, Point, db

class PointAction(Enum):
    ADD = 1
    SUBTRACT = -1
    UNDO = 0

class GameNotification(Enum):
    GAME_WON = "game_won"
    SET_WON = "set_won"
    MATCH_WON = "match_won"

class PadelScoreManager:
    def __init__(self, court_id):
        self.court_id = court_id
        self.blue_team, self.red_team = self._load_teams()
        self.current_state = self._load_current_state()
        self.notifications = []
        self._validate_teams()
    
    def _validate_teams(self):
        """Valida que los equipos estén correctamente configurados"""
        if not self.blue_team or not self.red_team:
            raise ValueError("Los equipos no están correctamente configurados para esta cancha")
        
        # Actualiza los nombres en el estado si no coinciden
        if self.current_state['puntos'].get('azul') is None:
            self.current_state['puntos']['azul'] = '0'
        if self.current_state['puntos'].get('rojo') is None:
            self.current_state['puntos']['rojo'] = '0'

    def _load_teams(self):
        """Carga los equipos y valida su existencia"""
        teams = Team.query.filter_by(court_id=self.court_id).order_by(Team.id).all()
        
        if len(teams) != 2:
            raise ValueError("La cancha debe tener exactamente 2 equipos")
        
        # Asignamos dinámicamente los equipos (azul siempre será el primero creado por convención)
        blue = teams[0]
        red = teams[1]
        
        # Opcional: puedes verificar nombres si lo prefieres
        # blue = next((t for t in teams if t.name.lower() == "azul"), teams[0])
        # red = next((t for t in teams if t.name.lower() == "rojo"), teams[1])
        
        return blue, red

    def _load_current_state(self):
        """Carga el estado actual incluyendo información de equipos"""
        last_point = Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).order_by(desc(Point.point_number)).first()

        if not last_point:
            return self._create_initial_state()
        
        state = self._point_to_state(last_point)
        return state

    def _validate_teams(self):
        """Valida que los equipos y sus jugadores estén correctamente configurados"""
        if not self.blue_team or not self.red_team:
            raise ValueError("Los equipos no están correctamente configurados para esta cancha")
        
        # Validar que ambos equipos tengan jugadores
        try:
            blue_players = self._get_team_players(self.blue_team.id)
            red_players = self._get_team_players(self.red_team.id)
        except ValueError as e:
            current_app.logger.error(f"Error validando jugadores: {str(e)}")
            raise ValueError("No se puede iniciar el partido: " + str(e))
        
        # Actualiza los nombres en el estado si no coinciden
        if self.current_state['puntos'].get('azul') is None:
            self.current_state['puntos']['azul'] = '0'
        if self.current_state['puntos'].get('rojo') is None:
            self.current_state['puntos']['rojo'] = '0'

    def _get_team_players(self, team_id):
        """Obtiene los jugadores de un equipo desde la base de datos"""
        from game.models import Player  # Importamos aquí para evitar circular imports
        
        players = Player.query.filter_by(team_id=team_id).all()
        
        if not players:
            raise ValueError(f"No hay jugadores registrados para el equipo con ID {team_id}")
        
        return [player.name for player in players]

    def _create_initial_state(self):
        """Crea el estado inicial con información de equipos"""
        return {
            'puntos': {'azul': '0', 'rojo': '0'},
            'juegos': {'azul': 0, 'rojo': 0},
            'sets': {'azul': 0, 'rojo': 0},
            'set_actual': 1,
            'juego_actual': 1,
            'servicio': 'azul',
            'estado_partido': 'En juego',
            'teams': {
                'azul': {
                    'id': self.blue_team.id,
                    'name': self.blue_team.name,
                    'players': self._get_team_players(self.blue_team.id)
                },
                'rojo': {
                    'id': self.red_team.id,
                    'name': self.red_team.name,
                    'players': self._get_team_players(self.red_team.id)
                }
            }
        }

    def _point_to_state(self, point):
        """Convierte un punto a estado incluyendo información de equipos"""
        state = {
            'puntos': {
                'azul': point.puntos_azul_padel,
                'rojo': point.puntos_rojo_padel
            },
            'juegos': {
                'azul': point.juegos_azul,
                'rojo': point.juegos_rojo
            },
            'sets': {
                'azul': point.sets_azul,
                'rojo': point.sets_rojo
            },
            'set_actual': point.set_actual,
            'juego_actual': point.juego_actual,
            'servicio': point.servicio,
            'estado_partido': point.estado_partido,
            'teams': {
                'azul': {
                    'id': self.blue_team.id,
                    'name': self.blue_team.name,
                    'players': self._get_team_players(self.blue_team.id)
                },
                'rojo': {
                    'id': self.red_team.id,
                    'name': self.red_team.name,
                    'players': self._get_team_players(self.red_team.id)
                }
            }
        }
        
        if hasattr(point, 'notifications'):
            state['notifications'] = point.notifications
            
        return state

    def procesar_senal(self, team_id, signal):
        """Método principal para sumar/restar puntos"""
        try:
            # Validar equipos y jugadores antes de procesar
            self._validate_teams()
            
            if signal not in [-1, 1]:
                raise ValueError("Señal inválida. Debe ser 1 (sumar) o -1 (restar)")

            if signal == -1:
                return self._handle_subtract_point(team_id)
            else:
                return self._handle_add_point(team_id)
                
        except ValueError as e:
            current_app.logger.error(f"Error procesando señal: {str(e)}")
            # Devolver el estado actual con el error
            state = self._get_full_state()
            state['error'] = str(e)
            return state

    def _handle_add_point(self, team_id):
        """Maneja la adición de un punto"""
        new_state = self._calculate_new_state(team_id, 1)
        new_point = self._create_point_record(team_id, 1, new_state)
        self._save_new_point(new_point)
        return self._get_full_state()

    def _handle_subtract_point(self, team_id):
        """Maneja la resta de un punto con lógica especial"""
        # Caso especial: si estamos al inicio de un nuevo juego/set
        if any(v == "0" for v in self.current_state['puntos'].values()):
            return self._revert_game_change()
        
        # Caso normal: restar punto dentro del mismo juego
        new_state = self._calculate_new_state(team_id, -1)
        new_point = self._create_point_record(team_id, -1, new_state)
        self._save_new_point(new_point)
        return self._get_full_state()

    def _revert_game_change(self):
        """Revierte un cambio de juego/set al restar un punto"""
        last_point = Point.query.filter(
            Point.court_id == self.court_id,
            Point.point_number < Point.query.filter_by(
                court_id=self.court_id,
                active=True
            ).order_by(desc(Point.point_number)).first().point_number
        ).order_by(desc(Point.point_number)).first()

        if not last_point:
            return self._get_full_state()

        # Reactivar punto anterior
        current_point = Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).first()
        if current_point:
            current_point.active = False
            db.session.add(current_point)

        last_point.active = True
        db.session.add(last_point)
        db.session.commit()

        self.current_state = self._point_to_state(last_point)
        return self._get_full_state()

    def _calculate_new_state(self, team_id, signal):
        state = self.current_state.copy()
        self.notifications = []

        point_values = {'0': 0, '15': 1, '30': 2, '40': 3, 'Ventaja': 4}
        reverse_map = {v: k for k, v in point_values.items()}

        blue_points = point_values.get(state['puntos']['azul'], 0)
        red_points = point_values.get(state['puntos']['rojo'], 0)

        if team_id == self.blue_team.id:
            blue_points += signal
            blue_points = max(0, blue_points)
        else:
            red_points += signal
            red_points = max(0, red_points)

        return self._determine_game_state(state, blue_points, red_points)

    def _determine_game_state(self, state, blue_points, red_points):
        point_diff = abs(blue_points - red_points)
        
        if (blue_points >= 4 and point_diff >= 2) or (red_points >= 4 and point_diff >= 2):
            winner = 'azul' if blue_points > red_points else 'rojo'
            return self._handle_game_win(state, winner)
        
        if blue_points >= 3 and red_points >= 3:
            if blue_points == red_points:
                state['puntos'] = {'azul': '40', 'rojo': '40', 'especial': 'Deuce'}
            elif blue_points == red_points + 1:
                state['puntos'] = {'azul': 'Ventaja', 'rojo': '40'}
            elif red_points == blue_points + 1:
                state['puntos'] = {'azul': '40', 'rojo': 'Ventaja'}
            return state
        
        point_map = {0: '0', 1: '15', 2: '30', 3: '40'}
        state['puntos'] = {
            'azul': point_map.get(blue_points, '0'),
            'rojo': point_map.get(red_points, '0')
        }
        return state

    def _handle_game_win(self, state, winner):
        state['juegos'][winner] += 1
        state['puntos'] = {'azul': '0', 'rojo': '0'}
        
        self.notifications.append({
            'type': GameNotification.GAME_WON.value,
            'team': winner,
            'games': state['juegos'][winner]
        })

        if (state['juegos'][winner] >= 6 and 
            (state['juegos'][winner] - state['juegos'][self._opponent(winner)] >= 2)) or \
           state['juegos'][winner] == 7:
            return self._handle_set_win(state, winner)

        state['servicio'] = self._opponent(state['servicio'])
        return state

    def _handle_set_win(self, state, winner):
        state['sets'][winner] += 1
        state['juegos'] = {'azul': 0, 'rojo': 0}
        state['set_actual'] += 1
        
        self.notifications.append({
            'type': GameNotification.SET_WON.value,
            'team': winner,
            'sets': state['sets'][winner]
        })

        if state['sets'][winner] >= 2:
            state['estado_partido'] = f'Ganador: Equipo {winner.capitalize()}'
            self.notifications.append({
                'type': GameNotification.MATCH_WON.value,
                'team': winner
            })

        return state

    def _opponent(self, team):
        return 'rojo' if team == 'azul' else 'azul'

    def _create_point_record(self, team_id, signal, state):
        last_point = Point.query.filter_by(court_id=self.court_id).order_by(desc(Point.point_number)).first()
        new_point_number = last_point.point_number + 1 if last_point else 1
        
        point = Point(
            court_id=self.court_id,
            team_id=team_id,
            signal_received=signal,
            point_number=new_point_number,
            puntos_azul_padel=state['puntos'].get('azul', '0'),
            puntos_rojo_padel=state['puntos'].get('rojo', '0'),
            juegos_azul=state['juegos']['azul'],
            juegos_rojo=state['juegos']['rojo'],
            sets_azul=state['sets']['azul'],
            sets_rojo=state['sets']['rojo'],
            set_actual=state['set_actual'],
            juego_actual=state['juego_actual'],
            servicio=state['servicio'],
            estado_partido=state['estado_partido'],
            active=True,
            timestamp=datetime.utcnow()
        )
        
        if self.notifications:
            point.notifications = [dict(n) for n in self.notifications]
            
        return point

    def _save_new_point(self, new_point):
        self._deactivate_previous_points()
        db.session.add(new_point)
        db.session.commit()
        self.current_state = self._point_to_state(new_point)

    def _deactivate_previous_points(self):
        Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).update({'active': False})

    def _get_full_state(self):
        """Devuelve el estado completo con información de equipos"""
        state = self.current_state.copy()
        
        # Asegurarse de que la información de equipos está incluida
        if 'teams' not in state:
            state['teams'] = {
                'azul': {
                    'id': self.blue_team.id,
                    'name': self.blue_team.name,
                    'players': self._get_team_players(self.blue_team.id)
                },
                'rojo': {
                    'id': self.red_team.id,
                    'name': self.red_team.name,
                    'players': self._get_team_players(self.red_team.id)
                }
            }
        
        if self.notifications:
            state['notifications'] = [n for n in self.notifications]
            self.notifications = []
        
        return state