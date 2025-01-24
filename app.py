from flask import Flask, jsonify
import os
from fullstack_project.backend.scripts.selenium_service import run_selenium_task
from routes.monitores import monitores_bp

app = Flask(__name__)

@app.route('/run-selenium', methods=['GET'])
def selenium_task():
    try:
        # Ejecuta la función que contiene la lógica de Selenium
        run_selenium_task()
        return jsonify({"message": "Selenium task completed successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Utiliza la variable de entorno PORT que proporciona Azure
    port = int(os.environ.get("PORT", 5002))
    app.run(host='0.0.0.0', port=port, debug=True)