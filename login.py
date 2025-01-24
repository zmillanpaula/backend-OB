import sys
import logging
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

def main():
    # Configuración del logger
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Definición de opciones para Chrome
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Inicialización del driver
    driver = None
    try:
        # Verificación de argumentos
        if len(sys.argv) < 3:
            logging.error("Uso: python3 login.py <username> <password>")
            sys.exit(1)

        username, password = sys.argv[1:]
        logging.info(f"Iniciando sesión con usuario: {username}")

        # Conexión al servidor Selenium
        driver = webdriver.Remote(
            command_executor="http://selenium:4444/wd/hub",  # URL del Hub de Selenium Grid
            options=options
        )
        logging.info("Driver inicializado correctamente.")

        # Navegar a la página de login
        driver.get("https://campusvirtual.bestwork.cl/login/index.php")
        logging.info("Página de inicio de sesión cargada.")

        # Interacción con los elementos de la página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys(username)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        ).send_keys(password)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginbtn"))
        ).click()

        logging.info("Formulario enviado, verificando el inicio de sesión...")

        # Verificar si el inicio de sesión fue exitoso
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//img[@src='https://campusvirtual.bestwork.cl/pluginfile.php/33745/block_html/content/BW%20-%20%C2%A1%C2%A1Bienvenido%21%21.jpg']"))  # Elemento que solo aparece tras iniciar sesión
            )
            logging.info("Inicio de sesión exitoso.")
            
            # Guardar cookies de sesión
            cookies = driver.get_cookies()
            with open("session_cookies.json", "w") as file:
                json.dump(cookies, file)
            logging.info("Cookies de sesión guardadas exitosamente.")

        except Exception:
            logging.error("Inicio de sesión fallido. Credenciales inválidas.")
            sys.exit(1)  # Salida con error si las credenciales son inválidas
    
    except Exception as e:
        logging.error(f"Error en el proceso de inicio de sesión: {e}")
        sys.exit(1)  # Salida con error para cualquier excepción
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()