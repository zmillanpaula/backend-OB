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

# Configuración de logs
logging.basicConfig(level=logging.INFO)


@app.route('/monitores', methods=['GET'])
def get_monitores():
    """
    Devuelve la lista de monitores predefinida.
    """
    monitores = [
        "Maureen Salinas", "Romina Pego", "Rubén Erazo", "Karen Bázaez",
        "Gabriela Vargas", "Bernardo Inostroza", "Bruno Palma", "Ivette Aguirre",
        "Andrés Molina", "Rocío Pérez", "Nelvia Mardones", "Jaime Rodríguez",
        "Bárbara Gangas", "Carmen Tebre", "Francisca Osorio", "Francisca Vera",
        "Damaris Ibarra", "Francois Gomez", "Victor Roa", "Sara Parra",
        "Vivian Lagos", "Tania Ferreira", "Valentina Pacheco", "Katherine Torres",
        "Pablo Mancilla", "Rodrigo Barrientos", "Maria Patricia Orellana", "Felipe Quilaqueo"
    ]
    return jsonify(monitores)

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

        logging.info(f"👤 Monitor seleccionado: {monitor}")
        logging.info(f"📧 Correo ingresado: {correo}")

        # 🔹 Obtener WebDriver activo o iniciar uno nuevo (login automático si es necesario)
        driver = selenium_manager.start_driver()

        # 🔹 Buscar estudiante en el sistema
        resultado = buscar_estudiante(driver, correo)

        # 🔹 Manejo de errores en la búsqueda
        if "error" in resultado:
            logging.warning(f"❌ Error en búsqueda: {resultado['error']}")
            return jsonify({"error": resultado["error"], "existe": resultado["existe"]}), 400

        # 🔹 Si el estudiante fue encontrado, guardamos el correo globalmente
        correo_global = correo
        logging.info(f"✅ Estudiante encontrado: {resultado}")

        return jsonify(resultado)

    except Exception as e:
        logging.exception(f"❌ Error en /buscar_estudiante: {e}")
        return jsonify({"error": "Ocurrió un error interno. Contacta al administrador."}), 500

@app.route('/asignar_nivel', methods=['POST'])
def asignar_nivel_endpoint():
    """
    Asigna un nivel básico al estudiante.
    """
    global correo_global
    global selenium_manager
    try:
        data = request.json
        nivel = data.get('nivel')

        if not all([correo_global, nivel]):
            return jsonify({"error": "Faltan datos requeridos"}), 400

        logging.info(f"Asignando nivel {nivel} al correo {correo_global}...")
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
    global selenium_manager, correo_global
    
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

        resultado = asignar_nivel_avanzado(driver, correo, nivel)

        logging.info(f"✅ Resultado asignación avanzada: {resultado}")
        return jsonify(resultado)

    except Exception as e:
        logging.error(f"❌ Error en /asignar_nivel_avanzado: {e}", exc_info=True)
        return jsonify({"error": "Ocurrió un error interno. Contacta al administrador."}), 500
    
@app.route('/limpiar_sesion', methods=['POST'])
def limpiar_sesion():
    global selenium_manager
    try:
        selenium_manager.quit_driver()
        return jsonify({"message": "Sesión de Selenium cerrada con éxito"}), 200
    except Exception as e:
        logging.exception(f"Error al limpiar la sesión: {e}")
        return jsonify({"error": "Error al limpiar la sesión"}), 500

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