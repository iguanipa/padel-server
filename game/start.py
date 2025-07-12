# game/services/start.py

from game.models import db, Court, Team
import os
from dotenv import load_dotenv
from game import logger
load_dotenv()

def verificar_o_poblar_datos():
    logger.info("Este log viene desde el módulo game")
    raw = os.getenv("CANCHAS")
    if not raw:
        print("⚠️ No se encontró la variable CANCHAS en el archivo .env.")
        return
    print(raw)
    
    if not Court.query.first():
        cancha = Court(name="Cancha Central")
        db.session.add(cancha)
        db.session.commit()
        print("✅ Se creó la cancha 'Cancha Central'.")

    if not Team.query.first():
        cancha = Court.query.first()
        equipo_azul = Team(name="Equipo Azul", court_id=cancha.id)
        equipo_rojo = Team(name="Equipo Rojo", court_id=cancha.id)
        db.session.add_all([equipo_azul, equipo_rojo])
        db.session.commit()
        print("✅ Se crearon los equipos Azul y Rojo.")
    else:
        print("✅ Ya existen registros de canchas y equipos.")
