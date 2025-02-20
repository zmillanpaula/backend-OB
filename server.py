import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv
import time
import logging
from selenium_manager import SeleniumManager
from sse_manager import obtener_eventos_sse, enviar_evento_sse, sse_clients
from buscar_estudiante import buscar_estudiante
from asignar_nivel import asignar_nivel_campus
from cerrar_onboarding import cerrar_onboarding_form
from asignar_nivel_avanzado import asignar_nivel_avanzado
from extraer_licencia import extraer_licencia_cambridge_sheets
from asignar_nivel_cambridge import invitacion_cambridge
from activeCampaignService import obtener_opciones_campo

# Configuración inicial
sys.path.append('/app/scripts')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

selenium_manager = SeleniumManager()  # Instancia global para manejar la sesión

estado_asignaciones = {}

load_dotenv()

GOOGLE_SHEETS_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY")

# Variables globales para almacenar temporalmente datos
correo_global = None
nivel_global = None
classKey_global = None
temp_storage = {"monitor": None}
estado_asignaciones = {} 

# Configuración de logs
logging.basicConfig(level=logging.INFO)


@app.route('/proxy_monitores')
def proxy_monitores():
    url = "https://sedsa.api-us1.com/api/3/fields/264/options"
    headers = {"Api-Token": "d2830a151e2d5ae79ee56b3bf8035c9728d27a1c75fbd2fe89eff5f11c57f078c0f93ae1"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/seleccion_monitor', methods=['POST'])
def guardar_seleccion():
    data = request.get_json()
    monitor = data.get('monitor')
    if not monitor:
        return jsonify({'error': 'Monitor no proporcionado'}), 400

    logging.info(f"Monitor seleccionado: {monitor}")
    return jsonify({'message': 'Selección guardada con éxito'}), 200

@app.route('/buscar_estudiante', methods=['POST'])
def buscar_estudiante_endpoint():
    global correo_global, selenium_manager  

    try:
        logging.info("📌 Endpoint /buscar_estudiante llamado.")

        data = request.json
        correo = data.get('correo')
        monitor = data.get('monitor')

        if not all([correo, monitor]):
            logging.error("⚠️ Faltan campos requeridos: correo o monitor.")
            return jsonify({"error": "Correo y monitor son requeridos"}), 400

        correo_global = None  # 🔹 Reiniciar correo_global para evitar datos previos

        logging.info(f"👤 Monitor seleccionado: {monitor}")
        logging.info(f"📧 Correo ingresado: {correo}")

        driver = selenium_manager.start_driver()
        resultado = buscar_estudiante(driver, correo)

        if "error" in resultado:
            logging.warning(f"❌ Error en búsqueda: {resultado['error']}")
            return jsonify({"error": resultado["error"], "existe": resultado["existe"]}), 400

        correo_global = correo  # 🔹 Guardamos el nuevo correo si se encuentra el estudiante
        logging.info(f"📌 Correo global almacenado: {correo_global}")

        return jsonify(resultado)

    except Exception as e:
        logging.exception(f"❌ Error en /buscar_estudiante: {e}")
        return jsonify({"error": "Ocurrió un error interno."}), 500

@app.route('/asignar_nivel_avanzado', methods=['POST'])
def asignar_nivel_avanzado_endpoint():
    global selenium_manager, correo_global, nivel_global  

    try:
        data = request.json
        logging.info(f"📩 Datos recibidos en /asignar_nivel_avanzado: {data}")  

        correo = data.get('correo')
        if not correo:
            logging.info(f"🔍 Revisando correo_global antes de usarlo: {correo_global}")
            correo = correo_global  # ✅ Solo usa correo_global si el frontend no lo envió

        nivel = data.get('nivel')

        if not correo or not nivel:
            logging.warning(f"⚠️ Datos incompletos. Recibido: correo={correo}, nivel={nivel}")
            return jsonify({"error": "Correo y nivel son requeridos"}), 400

        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}...")

        driver = selenium_manager.start_driver()
        correo_global = correo  # ✅ Almacenamos el correo en la variable global
        nivel_global = nivel

        resultado = asignar_nivel_avanzado(driver, correo, nivel)

        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /asignar_nivel_avanzado: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/obtener_licencia', methods=['POST'])
def obtener_licencia():
    global correo_global, nivel_global  

    try:
        data = request.get_json()
        correo = data.get("correo", correo_global)  
        nivel = data.get("nivel", nivel_global)  

        if not correo or not nivel:
            return jsonify({"error": "No se encontró un correo activo o nivel. Intente nuevamente."}), 400

        logging.info(f"🟢 Solicitando licencia para correo: {correo}, nivel: {nivel}")

        resultado = extraer_licencia_cambridge_sheets(correo, nivel)

        if "error" in resultado:
            return jsonify({
                "warning": "No hay licencias disponibles en este momento. Será enviada a su correo a la brevedad."
            }), 200

        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /obtener_licencia: {e}")
        return jsonify({"error": "Ocurrió un error interno. Contacta al administrador."}), 500

@app.route('/enviar_invitacion_cambridge', methods=['POST'])
def enviar_invitacion_cambridge_endpoint():
    global selenium_manager, correo_global, nivel_global  

    if not request.is_json:
        logging.warning("⚠️ La solicitud no tiene un Content-Type válido.")
        return jsonify({"error": "La solicitud debe ser de tipo 'application/json'."}), 415

    try:
        data = request.json
        logging.info(f"📩 Datos recibidos en /enviar_invitacion_cambridge: {data}")  

        correo = data.get("correo")
        if not correo:
            correo = correo_global  # ✅ Solo usa correo_global si no vino en el request

        nivel = data.get("nivel", nivel_global)

        if not correo or not nivel:
            logging.warning(f"⚠️ Correo o nivel faltantes en /enviar_invitacion_cambridge. Recibido: correo={correo}, nivel={nivel}")
            return jsonify({"error": "Correo y nivel son requeridos"}), 400

        logging.info(f"📌 Enviando invitación a Cambridge para {correo} en nivel {nivel}...")

        driver = selenium_manager.start_driver()
        resultado = invitacion_cambridge(driver, correo, nivel)

        if "error" in resultado:
            return jsonify(resultado), 400  

        classKey_global = resultado.get("classKey")  # ✅ Guardamos classKey globalmente

        return jsonify({"success": True, "classKey": classKey_global})

    except Exception as e:
        logging.error(f"❌ Error en /enviar_invitacion_cambridge: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500  
    
@app.route('/limpiar_sesion', methods=['POST'])
def limpiar_sesion():
    global selenium_manager, correo_global, nivel_global, classKey_global  

    try:
        selenium_manager.quit_driver()
        correo_global = None  
        nivel_global = None
        classKey_global = None

        return jsonify({"message": "Sesión cerrada y datos reiniciados con éxito"}), 200
    except Exception as e:
        return jsonify({"error": "Error al limpiar la sesión"}), 500

if __name__ == "__main__":
    selenium_manager = SeleniumManager()
    if selenium_manager.is_grid_ready():
        logging.info("✅ Selenium Grid está listo.")
    else:
        exit(1)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)