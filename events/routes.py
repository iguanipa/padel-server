from . import game_bp
from flask import jsonify
from .services import get_game_status

@app.route('/lorawan/event', methods=['POST'])
def recibir_evento_lora():
    data = request.get_json()
    print("📡 Evento recibido:", data)
    # Aquí puedes procesar o guardar el payload
    return jsonify({"status": "ok"}), 200