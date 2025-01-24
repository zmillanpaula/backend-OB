import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

def asignar_estudiante_cambridge(driver, nivel):
    """
    Asigna un estudiante a un curso en Cambridge LMS, manejando cursos enumerados si es necesario.
    """
    try:
        # Recuperar correo almacenado en sessionStorage
        logging.info("Obteniendo correo del estudiante desde sessionStorage.")
        correo = driver.execute_script("return sessionStorage.getItem('correo_estudiante');")
        if not correo:
            raise ValueError("No se encontró el correo en sessionStorage. Verifica el flujo de búsqueda.")

        logging.info(f"Correo recuperado: {correo}")

        # Transformar el nivel para búsqueda en Cambridge
        niveles_transformados = {
            "3A": "3A LOWER INTERMEDIATE (N5)",
            "4A": "4A UPPER INTERMEDIATE (N7)",
            "5A": "5A ADVANCED I (N9)",
            "6A": "6A PROFICIENT (11)"
        }
        curso_base = niveles_transformados.get(nivel)
        if not curso_base:
            raise ValueError(f"Nivel '{nivel}' no reconocido.")

        logging.info(f"Nivel transformado para Cambridge: {curso_base}")

        # Navegar a Cambridge LMS
        logging.info("Accediendo a Cambridge LMS.")
        driver.get("https://www.cambridgeone.org/login")

        # Dar tiempo para cargar la página completamente
        logging.info("Esperando que la página se cargue completamente.")
        time.sleep(5)  # Espera inicial adicional
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body"))  # Verificar que el cuerpo del HTML esté cargado
        )

        # Aceptar cookies si están presentes
        try:
            logging.info("Verificando el aviso de cookies.")
            cookies_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Accept cookies']"))
            )
            cookies_button.click()
            logging.info("Cookies aceptadas.")
            time.sleep(2)  # Espera breve para procesar el clic
        except TimeoutException:
            logging.info("No se encontró el aviso de cookies, continuando.")

        # Verificar disponibilidad de los campos de login
        logging.info("Verificando disponibilidad de campos de login.")
        username_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='username']"))
        )
        password_field = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='password']"))
        )

        # Ingresar credenciales
        try:
            logging.info("Ingresando credenciales.")
            username_field.clear()
            username_field.send_keys("activacionlicencia@bestwork.cl")
            password_field.clear()
            password_field.send_keys("Bestwork2021")
        except ElementNotInteractableException as e:
            driver.save_screenshot("login_field_not_interactable.png")
            raise ValueError(f"Error al interactuar con los campos de login: {e}")

        # Presionar el botón de inicio de sesión
        logging.info("Intentando presionar el botón de iniciar sesión.")
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Log in']"))
        )
        login_button.click()

        # Confirmar que la página redirige al dashboard
        try:
            logging.info("Esperando redirección al dashboard.")
            WebDriverWait(driver, 20).until(
                EC.url_contains("dashboard")
            )
            logging.info("Inicio de sesión exitoso y redirigido al dashboard.")
        except TimeoutException:
            driver.save_screenshot("dashboard_not_loaded.png")
            raise ValueError("No se redirigió al dashboard después del inicio de sesión.")

        # Continuar con el flujo de asignación de curso...

    except Exception as e:
        logging.error(f"Error en la asignación de estudiante: {e}")
        driver.save_screenshot("general_error.png")
        return {"error": str(e)}

    finally:
        # Cierra el navegador después de la operación
        driver.quit()