from flask import request  # Importación necesaria
from flask_socketio import SocketIO, emit, join_room, leave_room
from .models import db

# Variable global para SocketIO
socketio = None

def init_socketio(app):
    """Inicializa SocketIO con la app Flask."""
    global socketio
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='eventlet',
        logger=True,  # Para ver logs de conexión
        engineio_logger=True  # Logs detallados
    )
    register_events()
    return socketio

def register_events():
    """Registra todos los eventos WebSocket."""

    @socketio.on('connect')
    def handle_connect():
        from flask import session  # Ejemplo de importación local si necesitas session
        print(f'[WebSocket] Cliente conectado - SID: {request.sid}')

    @socketio.on('disconnect')
    def handle_disconnect():
        print(f'[WebSocket] Cliente desconectado - SID: {request.sid}')

    @socketio.on('unirse_cancha')
    def handle_unirse_cancha(data):
        cancha_id = data.get('cancha_id')
        if cancha_id:
            join_room(f'cancha_{cancha_id}')
            print(f'[WebSocket] Cliente {request.sid} unido a cancha_{cancha_id}')
            # Opcional: Enviar estado actual al nuevo cliente
            # emit('actualizar_marcador', data, room=request.sid)

    @socketio.on('dejar_cancha')
    def handle_dejar_cancha(data):
        cancha_id = data.get('cancha_id')
        if cancha_id:
            leave_room(f'cancha_{cancha_id}')
            print(f'[WebSocket] Cliente {request.sid} dejó cancha_{cancha_id}')

def emitir_actualizacion(cancha_id, data):
    """Emite actualizaciones a una cancha específica."""
    if socketio:
        socketio.emit(
            'actualizar_marcador',
            data,
            room=f'cancha_{cancha_id}',
            namespace='/'  # Usa el mismo namespace que la conexión
        )
        print(f'[WebSocket] Emitido a cancha_{cancha_id}: {data}')