import code
from game.models import db, Court, Team
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

def verificar_o_poblar_datos():
    logger.info("Iniciando verificación/población de datos")
    
    # Poblar canchas
    if not Court.query.first():
        raw = os.getenv("CANCHAS", "").split(',')
        if not raw or not raw[0]:
            logger.error("⚠️ No se encontró la variable CANCHAS en el archivo .env.")
            return
        
        for court in raw:
            nombre, codigo = court.split(';')
            if court.strip():  # Verifica que no esté vacío
                
                cancha = Court(name=nombre.strip(), code=codigo.strip())
                db.session.add(cancha)
        db.session.commit()
        logger.info(f"✅ Se crearon {len(raw)} canchas")
    else:
        logger.info("Las canchas ya existen en la base de datos")


    Team.query.delete()