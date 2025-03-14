import sys
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import os
import json
import requests
from dotenv import load_dotenv
import time
import logging
from selenium_manager import SeleniumManager
from sse_manager import obtener_eventos_sse, enviar_evento_sse, sse_clients
from buscar_estudiante import buscar_estudiante
from asignar_nivel import asignar_nivel_campus
from asignar_nivel_avanzado import asignar_nivel_avanzado
from extraer_licencia import extraer_licencia_cambridge_sheets
from asignar_nivel_cambridge import invitacion_cambridge
from cerrar_onboarding import cerrar_onboarding_form
from cierre_docencia import actualizar_fila_en_google_sheets
from activa_nivel_Serpo import test_guardar_observacion
from activeCampaignService import get_contact_with_details

sys.path.append('/app/scripts')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

selenium_manager = SeleniumManager()
estado_asignaciones = {}

load_dotenv()  # Cargar variables del archivo .env

# Leer la variable de entorno y convertirla en JSON
google_sheets_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

if google_sheets_credentials:
    try:
        creds_json = json.loads(google_sheets_credentials)
        print("✅ Credenciales cargadas correctamente")
    except json.JSONDecodeError as e:
        print(f"❌ Error al cargar credenciales: {e}")
else:
    print("❌ GOOGLE_SHEETS_CREDENTIALS no está definida en el entorno")

GOOGLE_SHEETS_API_KEY = os.getenv("GOOGLE_SHEETS_API_KEY")

# Variables globales para almacenar datos temporales
temp_storage = {}

logging.basicConfig(level=logging.INFO)

# 📌 🔹 **Endpoint para obtener monitores desde ActiveCampaign**
@app.route('/proxy_monitores')
def proxy_monitores():
    url = "https://sedsa.api-us1.com/api/3/fields/264/options"
    headers = {"Api-Token": os.getenv("ACTIVE_CAMPAIGN_API_KEY")}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

# 📌 🔹 **Endpoint para seleccionar monitor**
@app.route('/seleccion_monitor', methods=['POST'])
def guardar_seleccion():
    data = request.get_json()
    monitor = data.get('monitor')
    if not monitor:
        return jsonify({'error': 'Monitor no proporcionado'}), 400

    temp_storage["monitor"] = monitor  # 🔹 Guardamos el monitor seleccionado
    logging.info(f"✅ Monitor seleccionado y almacenado: {monitor}")

    return jsonify({'message': 'Selección guardada con éxito'}), 200

# 📌 🔹 **Endpoint para buscar estudiante**
@app.route('/buscar_estudiante', methods=['POST'])
def buscar_estudiante_endpoint():
    global selenium_manager  

    try:
        logging.info("📌 Endpoint /buscar_estudiante llamado.")

        data = request.json
        correo = data.get('correo')
        monitor = data.get('monitor', temp_storage.get("monitor"))  # 🔹 Intentamos obtener el monitor desde el request o temp_storage

        if not correo or not monitor:
            logging.error("⚠️ Correo y monitor son requeridos, pero no fueron proporcionados correctamente.")
            return jsonify({"error": "Correo y monitor son requeridos"}), 400

        logging.info(f"📧 Correo ingresado: {correo}")
        logging.info(f"👤 Monitor seleccionado: {monitor}")

        driver = selenium_manager.start_driver()
        resultado = buscar_estudiante(driver, correo)

        if "error" in resultado:
            return jsonify({"error": resultado["error"], "existe": resultado["existe"]}), 400

        # 🔹 Guardamos el correo en `temp_storage`
        temp_storage["email"] = correo  
        temp_storage["monitor"] = monitor  # 🔹 Ahora también guardamos el monitor si venía en la solicitud
        logging.info(f"✅ Correo y monitor almacenados en temp_storage: {correo}, {monitor}")

        return jsonify(resultado)

    except Exception as e:
        logging.exception(f"❌ Error en /buscar_estudiante: {e}")
        return jsonify({"error": "Ocurrió un error interno."}), 500

@app.route('/asignar_nivel', methods=['POST'])
def asignar_nivel_endpoint():
    global selenium_manager, temp_storage  

    try:
        data = request.json
        logging.info(f"📩 Datos recibidos en /asignar_nivel: {data}")  

        correo = temp_storage.get("email")  
        nivel = data.get("nivel")

        if not correo or not nivel:
            return jsonify({"error": "Correo y nivel son requeridos."}), 400

        driver = selenium_manager.start_driver()
        resultado = asignar_nivel_campus(driver, correo, nivel)

        temp_storage["nivel"] = nivel  # 🔹 Guardamos el nivel asignado

        # 🔹 Si es un nivel **básico**, asignamos valores predeterminados
        if nivel in ["1A", "1B", "2A", "2B"]:
            temp_storage["classKey"] = "NO_APLICA"
            temp_storage["codigo_licencia"] = "NO_APLICA"
            logging.info(f"✅ Nivel básico detectado. Se asigna 'NO_APLICA' a classKey y codigo_licencia.")

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 📌 🔹 **Endpoint para obtener licencia**
@app.route('/obtener_licencia', methods=['POST'])
def obtener_licencia():
    global temp_storage  

    try:
        correo = temp_storage.get("email")
        nivel = temp_storage.get("nivel")

        if not correo or not nivel:
            return jsonify({"error": "Correo y nivel requeridos"}), 400

        resultado = extraer_licencia_cambridge_sheets(correo, nivel)

        if "error" in resultado:
            temp_storage["codigo_licencia"] = "PENDIENTE"
            return jsonify({"warning": "Licencia no disponible, será enviada más tarde."}), 200

        temp_storage["codigo_licencia"] = resultado.get("codigo_licencia", "NO_APLICA")
        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": "Error interno."}), 500

@app.route('/enviar_invitacion_cambridge', methods=['POST'])
def enviar_invitacion_cambridge_endpoint():
    global selenium_manager, temp_storage  

    try:
        correo = temp_storage.get("email")
        nivel = temp_storage.get("nivel")

        if not correo or not nivel:
            return jsonify({"error": "Correo y nivel requeridos"}), 400

        driver = selenium_manager.start_driver()
        resultado = invitacion_cambridge(driver, correo, nivel)

        if "error" in resultado:
            return jsonify(resultado), 400  

        temp_storage["classKey"] = resultado.get("classKey", "NO_APLICA")
        return jsonify({"success": True, "classKey": temp_storage["classKey"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/obtener_datos_onboarding', methods=['POST'])
def obtener_datos_onboarding():
    """
    Obtiene los datos del estudiante desde ActiveCampaign.
    """
    global temp_storage  

    data = request.json or {}
    email = data.get("correo") or temp_storage.get("email")

    if not email:
        return jsonify({"error": "El correo es obligatorio y no se encontró en sesión."}), 400

    logging.info(f"📌 Buscando datos en ActiveCampaign para {email}")

    # 🔹 Obtener datos desde ActiveCampaign
    info = get_contact_with_details(email)

    if not info:
        logging.warning(f"⚠️ No se encontraron datos para {email} en ActiveCampaign.")
        return jsonify({"error": "No se encontró el estudiante en ActiveCampaign."}), 404

    # 🔹 Obtener número de contrato o asignar "7086" si no existe
    numero_contrato = info.get("numero_contrato") or "7086"

    # 🔹 Obtener meses contratados (por defecto 3 meses)
    meses_contratados = int(info.get("meses_contratados", 3))

    # 🔹 Calcular niveles contratados (dividimos por 3, asegurando mínimo 1)
    niveles_contratados = max(1, meses_contratados // 3)

    logging.info(f"🔎 Datos obtenidos - Número de contrato: {numero_contrato}, Meses contratados: {meses_contratados}, Niveles contratados: {niveles_contratados}")

    # 🔹 Guardamos en temp_storage
    temp_storage.update({
        "email": email,
        "rut": info.get("rut"),
        "nombre": info.get("nombre"),
        "apellido": info.get("apellido"),
        "numero_contrato": numero_contrato,
        "niveles_contratados": niveles_contratados,  # ✅ Ya calculado correctamente
    })

    logging.info(f"✅ Datos almacenados correctamente en temp_storage para {email}")

    return jsonify({
        "message": "✅ Datos obtenidos con éxito.",
        "datos": temp_storage
    }), 200
    
@app.route('/confirmar_cierre_onboarding', methods=['POST'])
def confirmar_cierre_onboarding():
    """Ejecuta la actualización de Google Sheets y el registro en SERPO después de la validación del monitor."""
    global temp_storage

    email = temp_storage.get("email")  
    nivel = temp_storage.get("nivel", "1A")  # ✅ Nivel por defecto si no está definido
    monitor = temp_storage.get("monitor", "Pruebas")
    numero_contrato = temp_storage.get("numero_contrato", "7086")  # ✅ Default a 7086 si no hay
    niveles_contratados = temp_storage.get("niveles_contratados", 1)

    if not email or not nivel or not monitor:
        logging.warning(f"⚠️ Faltan datos obligatorios: {email}, {nivel}, {monitor}")
        return jsonify({"error": "Faltan datos obligatorios."}), 400

    logging.info(f"📌 Confirmando cierre de onboarding para {email}")
    logging.info(f"  - Monitor: {monitor}")
    logging.info(f"  - Nivel: {nivel}")
    logging.info(f"  - Número de contrato: {numero_contrato}")
    logging.info(f"  - Niveles contratados: {niveles_contratados}")

    # ✅ Enviar datos a Google Sheets
    logging.info("🛠️ Enviando datos a Google Sheets...")
    resultado_sheets = actualizar_fila_en_google_sheets(email, nivel)
    logging.info(f"✅ Resultado Google Sheets: {resultado_sheets}")

    if "error" in resultado_sheets:
        logging.error(f"❌ Error en Google Sheets: {resultado_sheets['error']}")
        return jsonify(resultado_sheets), 500

    # ✅ Enviar datos a SERPO
    logging.info("🛠️ Enviando datos a SERPO...")
    resultado_serpo = test_guardar_observacion(nivel, niveles_contratados, numero_contrato)
    logging.info(f"✅ Resultado SERPO: {resultado_serpo}")

    if "error" in resultado_serpo:
        logging.error(f"❌ Error en SERPO: {resultado_serpo['error']}")
        return jsonify(resultado_serpo), 500

    return jsonify({
        "message": "✅ Cierre de onboarding completado.",
        "sheets": resultado_sheets,
        "serpo": resultado_serpo
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))