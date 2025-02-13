import time
import logging
from flask import Response

sse_clients = {}  # Diccionario de clientes SSE conectados

def enviar_evento_sse(correo, mensaje):
    """Envía un mensaje a los clientes conectados en tiempo real."""
    if correo not in sse_clients:
        logging.warning(f"⚠️ No hay clientes SSE conectados para {correo}.")
        return

    try:
        sse_clients[correo].write(f"data: {mensaje}\n\n")
        sse_clients[correo].flush()
        logging.info(f"📡 SSE enviado -> {correo}: {mensaje}")
    except Exception as e:
        logging.error(f"❌ Error enviando SSE a {correo}: {e}")

def obtener_eventos_sse(correo):
    """Maneja la conexión SSE para un correo específico."""
    def event_stream():
        try:
            while True:
                # 🔹 Si hay mensajes, los enviamos
                if correo in sse_clients and sse_clients[correo]:
                    mensaje = sse_clients[correo].pop(0)
                    yield f"data: {mensaje}\n\n"

                # 🔹 Enviar un "ping" cada 10s para evitar desconexión
                yield "data: [PING]\n\n"
                time.sleep(10)

        except GeneratorExit:
            logging.info(f"🔌 Cliente SSE desconectado: {correo}")
            sse_clients.pop(correo, None)  # Eliminar cliente al desconectarse

    response = Response(event_stream(), content_type="text/event-stream")
    sse_clients[correo] = []
    logging.info(f"✅ Cliente SSE conectado para {correo}")

    return response