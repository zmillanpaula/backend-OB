from flask import Response
import time
import logging

sse_clients = {}

def enviar_evento_sse(correo, mensaje):
    """Agrega un mensaje para el usuario y lo envía inmediatamente si hay una conexión activa."""
    if correo not in sse_clients:
        sse_clients[correo] = []
    sse_clients[correo].append(mensaje)
    logging.info(f"📡 SSE -> {correo}: {mensaje}")

def obtener_eventos_sse(correo):
    """Genera un stream de eventos SSE para el correo especificado."""
    def event_stream():
        while True:
            if correo in sse_clients and sse_clients[correo]:
                mensaje = sse_clients[correo].pop(0)
                yield f"data: {mensaje}\n\n"
                logging.info(f"📤 Enviando SSE -> {correo}: {mensaje}")
            time.sleep(1)

    return Response(event_stream(), content_type="text/event-stream")