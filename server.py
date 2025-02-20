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

        # 🔹 Reiniciar correo_global para evitar datos previos
        correo_global = None  

        logging.info(f"👤 Monitor seleccionado: {monitor}")
        logging.info(f"📧 Correo ingresado: {correo}")

        driver = selenium_manager.start_driver()
        resultado = buscar_estudiante(driver, correo)

        if "error" in resultado:
            logging.warning(f"❌ Error en búsqueda: {resultado['error']}")
            return jsonify({"error": resultado["error"], "existe": resultado["existe"]}), 400

        # 🔹 Guardamos el nuevo correo solo si se encuentra el estudiante
        correo_global = correo
        logging.info(f"📌 Correo global almacenado: {correo_global}")

        return jsonify(resultado)

    except Exception as e:
        logging.exception(f"❌ Error en /buscar_estudiante: {e}")
        return jsonify({"error": "Ocurrió un error interno."}), 500

@app.route('/asignar_nivel', methods=['POST'])
def asignar_nivel_endpoint():
    global correo_global, selenium_manager
    try:
        data = request.json
        nivel = data.get('nivel')

        if not correo_global:
            logging.error("⚠️ No hay correo disponible en la sesión.")
            return jsonify({"error": "No se encontró un correo activo. Inicie una nueva búsqueda."}), 400

        if not nivel:
            return jsonify({"error": "Nivel es requerido"}), 400

        logging.info(f"📌 Asignando nivel {nivel} a {correo_global}...")
        driver = selenium_manager.start_driver()
        resultado = asignar_nivel_campus(driver, correo_global, nivel)
        
        return jsonify(resultado)
    except Exception as e:
        logging.error(f"Error en /asignar_nivel: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/asignar_nivel_avanzado', methods=['POST'])
def asignar_nivel_avanzado_endpoint():
    """
    Endpoint para asignar un nivel avanzado a un estudiante en Campus Virtual.
    """
    global selenium_manager, correo_global, nivel_global
    
    try:
        data = request.json
        correo = data.get('correo')
        nivel = data.get('nivel')

        if not correo:
            correo = correo_global  # Usa correo_global solo si no se recibe en el request

        if not correo or not nivel:
            return jsonify({"error": "Correo y nivel son requeridos"}), 400

        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}...")

        # Llamamos a Selenium para asignar nivel
        try:
            driver = selenium_manager.start_driver()
        except Exception as e:
            logging.error(f"❌ Error al iniciar WebDriver: {e}", exc_info=True)
            return jsonify({"error": "No se pudo iniciar el WebDriver. Verifica Selenium Grid."}), 500
        
        nivel_global = nivel
        correo_global = correo

        resultado = asignar_nivel_avanzado(driver, correo, nivel)
        
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /asignar_nivel_avanzado: {e}")
        return jsonify({"error": str(e)}), 500
    

@app.route('/obtener_licencia', methods=['POST'])
def obtener_licencia():
    global correo_global  

    try:
        data = request.get_json()
        correo = data.get("correo", correo_global)  
        nivel = data.get("nivel")

        if not nivel:
            logging.warning("⚠️ Nivel no proporcionado.")
            return jsonify({"error": "Nivel es requerido"}), 400

        if not correo:
            logging.warning("⚠️ No hay un correo registrado en la sesión ni en la petición.")
            return jsonify({"error": "No se encontró un correo activo. Intente nuevamente."}), 400

        logging.info(f"🟢 Solicitando licencia para correo: {correo}, nivel: {nivel}")

        # ✅ Llamamos a la función de extracción de licencia
        resultado = extraer_licencia_cambridge_sheets(correo, nivel)

        if "error" in resultado:
            logging.warning(f"⚠️ No se encontraron licencias disponibles en stock.")
            return jsonify({
                "warning": "No hay licencias disponibles en este momento. Será enviada a su correo a la brevedad."
            }), 200

        logging.info(f"✅ Licencia obtenida con éxito: {resultado}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /obtener_licencia: {e}")
        return jsonify({"error": "Ocurrió un error interno. Contacta al administrador."}), 500

@app.route('/enviar_invitacion_cambridge', methods=['POST'])
def enviar_invitacion_cambridge_endpoint():
    """
    Endpoint para enviar una invitación a Cambridge y obtener la classKey.
    """
    global selenium_manager, correo_global, nivel_global  

    if not request.is_json:
        logging.warning("⚠️ La solicitud no tiene un Content-Type válido.")
        return jsonify({"error": "La solicitud debe ser de tipo 'application/json'."}), 415

    try:
        data = request.json
        correo = data.get("correo", correo_global)
        nivel = data.get("nivel", nivel_global)

        if not correo or not nivel:
            logging.warning("⚠️ Correo o nivel faltantes en la sesión.")
            return jsonify({"error": "Correo y nivel son requeridos"}), 400

        logging.info(f"📌 Enviando invitación a Cambridge para {correo} en nivel {nivel}...")

        driver = selenium_manager.start_driver()
        resultado = invitacion_cambridge(driver, correo, nivel)

        if "error" in resultado:
            return jsonify(resultado), 400  # Si hubo error en Cambridge, lo devolvemos

        # ✅ Guardamos classKey en la sesión temporal (opcional)
        classKey_global = resultado.get("classKey")

        return jsonify({"success": True, "classKey": classKey_global})

    except Exception as e:
        logging.error(f"❌ Error en /enviar_invitacion_cambridge: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500  
    
@app.route('/limpiar_sesion', methods=['POST'])
def limpiar_sesion():
    global selenium_manager, correo_global  # Agregar correo_global
    try:
        selenium_manager.quit_driver()
        correo_global = None  # 🔹 Reiniciar la variable global
        return jsonify({"message": "Sesión cerrada y datos reiniciados con éxito"}), 200
    except Exception as e:
        logging.exception(f"Error al limpiar la sesión: {e}")
        return jsonify({"error": "Error al limpiar la sesión"}), 500

@app.route('/estado_asignacion_stream', methods=['GET'])
def estado_asignacion_stream():
    correo = request.args.get("correo")
    if not correo:
        return jsonify({"error": "Correo requerido para SSE"}), 400

    return obtener_eventos_sse(correo)

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "¡Bienvenido al servidor Flask!"})




if __name__ == "__main__":
    # Instancia de SeleniumManager para verificar el estado de Selenium Grid
    selenium_manager = SeleniumManager()
    if selenium_manager.is_grid_ready():
        logging.info("✅ Selenium Grid está listo para aceptar conexiones.")
    else:
        logging.error("❌ Selenium Grid no está listo. Verifica la configuración.")
        # Opcionalmente puedes detener el servidor si Selenium no está disponible.
        exit(1)

    # Lee el puerto desde la variable de entorno PORT o usa 5002 como predeterminado
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)