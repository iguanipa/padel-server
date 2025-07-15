from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Court(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    code = db.Column(db.String(50))

# models.py
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    color = db.Column(db.String(10))  # 'azul' o 'rojo'
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))
    players = db.relationship('Player', backref='team', lazy=True)

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Point(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))
    signal_received = db.Column(db.Integer)  # puede ser +1 o -1
    point_number = db.Column(db.Integer)

    # Estado textual del marcador estilo pádel (visual, no contador interno)
    puntos_azul_padel = db.Column(db.String(20))
    puntos_rojo_padel = db.Column(db.String(20))

    # Estado acumulado del partido
    juegos_azul = db.Column(db.Integer)
    juegos_rojo = db.Column(db.Integer)
    sets_azul = db.Column(db.Integer)
    sets_rojo = db.Column(db.Integer)
    set_actual = db.Column(db.Integer)
    juego_actual = db.Column(db.Integer)
    servicio = db.Column(db.String(50))
    estado_partido = db.Column(db.String(50))

    active = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


