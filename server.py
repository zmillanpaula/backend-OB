import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from selenium_manager import SeleniumManager
from buscar_estudiante import buscar_estudiante
from asignar_nivel import asignar_nivel_campus
import logging
from cerrar_onboarding import cerrar_onboarding_form
from asignar_nivel_avanzado import asignar_nivel_avanzado
from extraer_licencia import extraer_licencia_cambridge_sheets
from asignar_nivel_cambridge import asignar_estudiante_cambridge
from activeCampaignService import obtener_opciones_campo
import os

# Configuración inicial
sys.path.append('/app/scripts')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

selenium_manager = SeleniumManager()  # Instancia global para manejar la sesión

# Variables globales para almacenar temporalmente datos
correo_global = None
temp_storage = {"monitor": None}
estado_asignaciones = {}  # 🔹 Nueva variable para almacenar estados de asignación

# Configuración de logs
logging.basicConfig(level=logging.INFO)

@app.route('/estado_asignacion', methods=['GET'])
def estado_asignacion():
    """
    Devuelve el estado actual de la asignación para un correo específico.
    """
    correo = request.args.get("correo")
    if not correo:
        return jsonify({"error": "Correo no proporcionado"}), 400

    estado = estado_asignaciones.get(correo, {"completado": False})  # Default: False
    return jsonify(estado)

@app.route('/actualizar_estado', methods=['POST'])
def actualizar_estado():
    """
    Actualiza el estado de la asignación cuando Selenium finaliza.
    """
    data = request.get_json()
    correo = data.get("correo")
    completado = data.get("completado", False)
    detalles = data.get("details", [])

    if not correo:
        return jsonify({"error": "Correo no proporcionado"}), 400

    estado_asignaciones[correo] = {"completado": completado, "details": detalles}
    return jsonify({"message": "Estado actualizado correctamente"})

@app.route('/asignar_nivel_avanzado', methods=['POST'])
def asignar_nivel_avanzado_endpoint():
    """
    Endpoint para asignar un nivel avanzado a un estudiante en Campus Virtual.
    """
    global selenium_manager, correo_global
    
    try:
        data = request.json
        correo = data.get("correo")
        nivel = data.get("nivel")

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

        resultado = asignar_nivel_avanzado(driver, correo, nivel)

        # 🔹 Cuando Selenium termina, actualizamos el estado
        estado_asignaciones[correo] = {"completado": True, "details": resultado.get("details", [])}
        logging.info(f"✅ Resultado asignación avanzada: {resultado}")

        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /asignar_nivel_avanzado: {e}", exc_info=True)
        return jsonify({"error": "Ocurrió un error interno. Contacta al administrador."}), 500

if __name__ == "__main__":
    selenium_manager = SeleniumManager()
    if selenium_manager.is_grid_ready():
        logging.info("✅ Selenium Grid está listo para aceptar conexiones.")
    else:
        logging.error("❌ Selenium Grid no está listo. Verifica la configuración.")
        exit(1)

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)