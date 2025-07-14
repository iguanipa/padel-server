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
        self.notifications = []  # Para almacenar eventos especiales

    def _load_teams(self):
        teams = Team.query.filter_by(court_id=self.court_id).all()
        if len(teams) != 2:
            raise ValueError("La cancha debe tener exactamente 2 equipos")
        
        blue = next((t for t in teams if t.name.lower() == "azul"), teams[0])
        red = next((t for t in teams if t.name.lower() == "rojo"), teams[1])
        return blue, red

    def _load_current_state(self):
        last_point = Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).order_by(desc(Point.point_number)).first()

        if not last_point:
            return {
                'puntos': {'azul': '0', 'rojo': '0'},
                'juegos': {'azul': 0, 'rojo': 0},
                'sets': {'azul': 0, 'rojo': 0},
                'set_actual': 1,
                'juego_actual': 1,
                'servicio': 'azul',
                'estado_partido': 'En juego'
            }

        return self._point_to_state(last_point)

    def _point_to_state(self, point):
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
            'estado_partido': point.estado_partido
        }
        
        # Agregar notificaciones si existen en el punto
        if hasattr(point, 'notifications'):
            state['notifications'] = point.notifications
            
        return state
    
    def process_action(self, team_id, action):
        """Procesa una acción (ADD, SUBTRACT o UNDO)"""
        if action == PointAction.UNDO:
            return self._undo_last_action()
        
        if team_id not in [self.blue_team.id, self.red_team.id]:
            raise ValueError("ID de equipo inválido")

        # Convertir acción a señal numérica
        signal = action.value
        
        # Calcular nuevo estado
        new_state = self._calculate_new_state(team_id, signal)
        
        # Guardar nuevo punto
        new_point = self._create_point_record(team_id, signal, new_state)
        self._deactivate_previous_points()
        
        db.session.add(new_point)
        db.session.commit()
        
        self.current_state = new_state
        return self._get_full_state()

    def _calculate_new_state(self, team_id, signal):
        state = self.current_state.copy()
        self.notifications = []
        
        # Mapeo de valores de puntos
        point_values = {'0': 0, '15': 1, '30': 2, '40': 3, 'Ventaja': 4}
        
        # Obtener puntos actuales
        blue_points = point_values.get(state['puntos']['azul'], 0)
        red_points = point_values.get(state['puntos']['rojo'], 0)

        # Manejo explícito de la señal
        if signal == -1:  # RESTAR PUNTO
            if team_id == self.blue_team.id and blue_points > 0:
                blue_points -= 1
            elif team_id == self.red_team.id and red_points > 0:
                red_points -= 1
        elif signal == 1:  # SUMAR PUNTO
            if team_id == self.blue_team.id:
                blue_points += 1
            else:
                red_points += 1
        
        # Convertir de vuelta a formato Pádel
        point_map = {0: '0', 1: '15', 2: '30', 3: '40'}
        state['puntos']['azul'] = point_map.get(blue_points, '0')
        state['puntos']['rojo'] = point_map.get(red_points, '0')
        
        # Resto de la lógica (juegos, sets, etc.)
        return self._determine_game_state(state, blue_points, red_points)

    def _get_full_state(self):
        """Devuelve el estado actual con notificaciones"""
        state = self.current_state.copy()
        if self.notifications:
            state['notifications'] = [n for n in self.notifications]
            self.notifications = []  # Limpiar notificaciones
        return state

   

    def _determine_game_state(self, state, blue_points, red_points):
        point_diff = abs(blue_points - red_points)
        
        # Caso: Juego ganado
        if (blue_points >= 4 and point_diff >= 2) or (red_points >= 4 and point_diff >= 2):
            winner = 'azul' if blue_points > red_points else 'rojo'
            return self._handle_game_win(state, winner)
        
        # Caso: Deuce o ventaja
        if blue_points >= 3 and red_points >= 3:
            if blue_points == red_points:
                state['puntos'] = {'azul': '40', 'rojo': '40', 'especial': 'Deuce'}
            elif blue_points == red_points + 1:
                state['puntos'] = {'azul': 'Ventaja', 'rojo': '40'}
            elif red_points == blue_points + 1:
                state['puntos'] = {'azul': '40', 'rojo': 'Ventaja'}
            return state
        
        # Puntos normales
        point_map = {0: '0', 1: '15', 2: '30', 3: '40'}
        state['puntos'] = {
            'azul': point_map.get(blue_points, '0'),
            'rojo': point_map.get(red_points, '0')
        }
        return state

    def _handle_game_win(self, state, winner):
        # Incrementar juegos
        state['juegos'][winner] += 1
        
        # Notificar juego ganado
        self.notifications.append({
            'type': GameNotification.GAME_WON.value,
            'team': winner,
            'games': state['juegos'][winner],
            'current_games': state['juegos']
        })

        # Resetear puntos (sin usar "Juego")
        state['puntos'] = {'azul': '0', 'rojo': '0'}

        # Verificar si se ganó el set
        if (state['juegos'][winner] >= 6 and 
            (state['juegos'][winner] - state['juegos'][self._opponent(winner)] >= 2)) or \
           state['juegos'][winner] == 7:
            return self._handle_set_win(state, winner)

        # Alternar servicio
        state['servicio'] = self._opponent(state['servicio'])
        return state

    def _handle_set_win(self, state, winner):
        # Incrementar sets
        state['sets'][winner] += 1
        
        # Notificar set ganado
        self.notifications.append({
            'type': GameNotification.SET_WON.value,
            'team': winner,
            'sets': state['sets'][winner],
            'current_sets': state['sets']
        })

        # Resetear juegos
        state['juegos'] = {'azul': 0, 'rojo': 0}
        state['set_actual'] += 1

        # Verificar si se ganó el partido
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
        
        # Guardar notificaciones en el punto
        if self.notifications:
            point.notifications = [dict(n) for n in self.notifications]
            
        return point

    def _deactivate_previous_points(self):
        Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).update({'active': False})

    def _undo_last_action(self):
        current_point = Point.query.filter_by(
            court_id=self.court_id,
            active=True
        ).order_by(desc(Point.point_number)).first()

        if not current_point:
            raise ValueError("No hay puntos para deshacer")

        # Encontrar punto anterior
        previous_point = Point.query.filter(
            Point.court_id == self.court_id,
            Point.point_number < current_point.point_number
        ).order_by(desc(Point.point_number)).first()

        # Desactivar punto actual
        current_point.active = False
        db.session.add(current_point)

        if previous_point:
            # Reactivar punto anterior
            previous_point.active = True
            db.session.add(previous_point)
            self.current_state = self._point_to_state(previous_point)
        else:
            # Si no hay puntos anteriores, volver al estado inicial
            self.current_state = {
                'puntos': {'azul': '0', 'rojo': '0'},
                'juegos': {'azul': 0, 'rojo': 0},
                'sets': {'azul': 0, 'rojo': 0},
                'set_actual': 1,
                'juego_actual': 1,
                'servicio': 'azul',
                'estado_partido': 'En juego'
            }

        db.session.commit()
        return self._get_full_state()