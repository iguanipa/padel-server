from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from game import game_bp
from game.models import db
import logging
from game.start import verificar_o_poblar_datos

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

logging.basicConfig(
    level=logging.INFO,  # Puedes usar DEBUG, WARNING, ERROR, etc.
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app.register_blueprint(game_bp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all() 
        verificar_o_poblar_datos()
    app.run(debug=True)
    