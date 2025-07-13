from flask import current_app
from sqlalchemy import desc
from datetime import datetime
from game.models import Team, Point, db

class MatchStateBuilder:
    def get_teams_by_court(self, court_id):
        teams = Team.query.filter_by(court_id=court_id).all()
        print(f"[get_teams_by_court] Equipos encontrados: {[t.name for t in teams]}")
        if len(teams) != 2:
            raise Exception("Se requieren exactamente 2 equipos en la cancha")
        azul = next((t for t in teams if t.name.lower() == "azul"), teams[0])
        rojo = next((t for t in teams if t.name.lower() == "rojo"), teams[1])
        print(f"[get_teams_by_court] Equipo azul ID: {azul.id}, Equipo rojo ID: {rojo.id}")
        return azul, rojo

    def get_historial(self, court_id):
        historial = Point.query.filter_by(court_id=court_id).order_by(Point.point_number.asc()).all()
        print(f"[get_historial] Total puntos en historial: {len(historial)}")
        return historial

    def calcular_puntos_padel(self, historial, azul_id, rojo_id):
        print(f"[calcular_puntos_padel] Procesando {len(historial)} puntos")
        secuencia = []
        for punto in historial:
            print(f"  - signal={punto.signal_received} team_id={punto.team_id}")
            if punto.signal_received == 1:
                secuencia.append(punto.team_id)
            elif punto.signal_received == -1:
                idx = next((i for i in reversed(range(len(secuencia))) if secuencia[i] == punto.team_id), None)
                if idx is not None:
                    secuencia.pop(idx)

        puntos_azul = sum(1 for t in secuencia if t == azul_id)
        puntos_rojo = sum(1 for t in secuencia if t == rojo_id)
        print(f"[calcular_puntos_padel] Contador actual → Azul: {puntos_azul}, Rojo: {puntos_rojo}")

        conversion = {0: "0", 1: "15", 2: "30", 3: "40"}
        if puntos_azul >= 3 and puntos_rojo >= 3:
            if puntos_azul == puntos_rojo:
                return {"azul": "40", "rojo": "40", "especial": "Deuce"}
            elif puntos_azul == puntos_rojo + 1:
                return {"azul": "Ventaja", "rojo": "40"}
            elif puntos_rojo == puntos_azul + 1:
                return {"azul": "40", "rojo": "Ventaja"}
            elif abs(puntos_azul - puntos_rojo) >= 2:
                ganador = "azul" if puntos_azul > puntos_rojo else "rojo"
                return {"azul": "Juego" if ganador == "azul" else "0", "rojo": "Juego" if ganador == "rojo" else "0"}

        return {
            "azul": conversion.get(puntos_azul, "0"),
            "rojo": conversion.get(puntos_rojo, "0")
        }

    def build_state(self, court_id):
        azul, rojo = self.get_teams_by_court(court_id)
        historial = self.get_historial(court_id)

        if not historial:
            print("[build_state] Sin historial, devolviendo estado inicial")
            return {
                "puntos": {"azul": "0", "rojo": "0"},
                "juegos": {"azul": 0, "rojo": 0},
                "sets": {"azul": 0, "rojo": 0},
                "setActual": 1,
                "juegoActual": 1,
                "estadoPartido": "En juego"
            }

        ultimo = historial[-1]
        print(f"[build_state] Último punto #: {ultimo.point_number}")
        print(f"[build_state] Marcador azul: {ultimo.puntos_azul_padel}, rojo: {ultimo.puntos_rojo_padel}")
        return {
            "puntos": {
                "azul": ultimo.puntos_azul_padel,
                "rojo": ultimo.puntos_rojo_padel
            },
            "juegos": {"azul": ultimo.juegos_azul, "rojo": ultimo.juegos_rojo},
            "sets": {"azul": ultimo.sets_azul, "rojo": ultimo.sets_rojo},
            "setActual": ultimo.set_actual,
            "juegoActual": ultimo.juego_actual,
            "estadoPartido": ultimo.estado_partido
        }

    def procesar_senal(self, court_id, team_id, signal):
        azul, rojo = self.get_teams_by_court(court_id)
        ultimo = Point.query.filter_by(court_id=court_id).order_by(desc(Point.point_number)).first()
        historial = self.get_historial(court_id)

        print(f"[procesar_senal] Señal recibida: {signal}, team_id: {team_id}")
        print(f"[procesar_senal] Último punto: {ultimo.point_number if ultimo else 'ninguno'}")

        simulado = historial + [Point(team_id=team_id, signal_received=signal)]
        traducidos = self.calcular_puntos_padel(simulado, azul.id, rojo.id)
        print(f"[procesar_senal] Resultado traducido: azul={traducidos['azul']}, rojo={traducidos['rojo']}")

        nuevo = Point(
            court_id=court_id,
            team_id=team_id,
            signal_received=signal,
            point_number=(ultimo.point_number + 1) if ultimo else 1,
            puntos_azul_padel=traducidos["azul"],
            puntos_rojo_padel=traducidos["rojo"],
            juegos_azul=ultimo.juegos_azul if ultimo else 0,
            juegos_rojo=ultimo.juegos_rojo if ultimo else 0,
            sets_azul=ultimo.sets_azul if ultimo else 0,
            sets_rojo=ultimo.sets_rojo if ultimo else 0,
            set_actual=ultimo.set_actual if ultimo else 1,
            juego_actual=ultimo.juego_actual if ultimo else 1,
            servicio=ultimo.servicio if ultimo else "azul",
            estado_partido=ultimo.estado_partido if ultimo else "En juego",
            active=True,
            timestamp=datetime.utcnow()
        )

        try:
            db.session.add(nuevo)
            db.session.commit()
            print(f"[procesar_senal] ✅ Punto guardado correctamente: ID {nuevo.id}")
            return self.build_state(court_id)
        except Exception as e:
            db.session.rollback()
            print(f"[procesar_senal] ❌ Error al guardar el punto: {str(e)}")
            return {"error": f"No se pudo guardar el punto: {str(e)}"}
