from flask import Flask
from game import game_bp
from game.models import db
import logging
from game.start import verificar_o_poblar_datos
import os  # Añade esta línea
from flask_socketio import SocketIO, emit
from game.sockets import init_socketio  # Importa la función de inicialización

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///game.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

socketio = init_socketio(app)  # 👈 Aquí se configura

db.init_app(app)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app.register_blueprint(game_bp)

if __name__ == "__main__":
    with app.app_context():
        # Elimina la base de datos existente si existe
        db_file = 'instance/game.db' if os.path.exists('instance') else 'game.db'
        if os.path.exists(db_file):
            os.remove(db_file)
            logging.info("🗑️ Base de datos eliminada")
        
        db.create_all()
        verificar_o_poblar_datos()
    socketio.run(app, debug=True, host='0.0.0.0')