from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Court(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    code = db.Column(db.String(50))

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))  # Ej: “Azul” o “Rojo”
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    court_id = db.Column(db.Integer, db.ForeignKey('court.id'))
    team_a_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team_b_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    date = db.Column(db.DateTime)

class Set(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    number = db.Column(db.Integer)
    points_team_a = db.Column(db.Integer)
    points_team_b = db.Column(db.Integer)
    active = db.Column(db.Boolean, default=False)
