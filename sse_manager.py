import time
import logging
from flask import Response

# 📌 Almacena los eventos SSE para cada usuario
sse_clients = {}

def enviar_evento_sse(correo, mensaje):
    """Guarda un mensaje en la lista de eventos SSE para un correo."""
    if correo not in sse_clients:
        sse_clients[correo] = []
    sse_clients[correo].append(mensaje)
    logging.info(f"📡 SSE -> {mensaje}")

def obtener_eventos_sse(correo):
    """Devuelve eventos SSE almacenados para un correo."""
    def event_stream():
        while True:
            if correo in sse_clients and sse_clients[correo]:
                mensaje = sse_clients[correo].pop(0)
                yield f"data: {mensaje}\n\n"
            time.sleep(1)  # Evita consumo excesivo de CPU

    return Response(event_stream(), content_type="text/event-stream")