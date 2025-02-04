import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class SeleniumManager:
    def __init__(self, grid_url=None):
        self.driver = None
        self.grid_url = grid_url or os.environ.get("SELENIUM_GRID_URL", "http://localhost:4444/wd/hub")

    def start_driver(self):
        """
        Inicializa el WebDriver. Si existe una sesión previa, la cierra antes de iniciar una nueva.
        """
        # 🔴 Cierra cualquier sesión previa antes de iniciar una nueva
        if self.driver:
            try:
                self.driver.quit()
                logging.info("⚠️ Cerrando sesión anterior antes de iniciar una nueva...")
            except Exception as e:
                logging.warning(f"⚠️ No se pudo cerrar la sesión anterior: {e}")
            finally:
                self.driver = None  # Resetear variable

        try:
            options = Options()
            
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--allow-insecure-localhost")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1280x800")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-infobars")
            options.add_argument("--single-process")
            options.add_argument("--disable-breakpad")
            options.add_argument("--disable-crash-reporter")
            options.add_argument("--disable-logging")
            options.add_argument("--disable-features=NetworkService")  # 🔹 Evita problemas de red en Railway
            options.add_argument("--disable-dev-shm-usage")  # Evita usar `/dev/shm`
            options.add_argument("--disable-features=VizDisplayCompositor") # Reduce uso gráfico

            # 🚀 Inicia el WebDriver con las opciones configuradas
            self.driver = webdriver.Remote(command_executor=self.grid_url, options=options)
            logging.info("✅ WebDriver iniciado correctamente.")

            # 📌 Intentar recuperar sessionStorage si la sesión se cerró
            self.recuperar_session_storage()

            # 🔑 Realizar login automático si es necesario
            self.hacer_login()

            return self.driver
        except Exception as e:
            logging.error(f"❌ Error al iniciar el WebDriver: {e}")
            raise

    def hacer_login(self):
        """
        Inicia sesión automáticamente en Campus Virtual.
        """
        try:
            logging.info("🔑 Iniciando sesión en Campus Virtual...")
            self.driver.get("https://campusvirtual.bestwork.cl/login")

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            ).send_keys("189572484")
            self.driver.find_element(By.ID, "password").send_keys("Mp18957248-4")
            self.driver.find_element(By.ID, "loginbtn").click()

            logging.info("✅ Login automático completado.")
        except Exception as e:
            logging.error(f"❌ Error durante el login: {e}")

    def recuperar_session_storage(self):
        """
        Intenta recuperar el correo desde `sessionStorage` si la sesión anterior se cerró.
        """
        try:
            logging.info("📌 Intentando recuperar sessionStorage...")
            self.driver.get("https://campusvirtual.bestwork.cl")
            correo = self.driver.execute_script("return sessionStorage.getItem('correo_estudiante');")
            if correo:
                logging.info(f"📌 Correo recuperado de sessionStorage: {correo}")
            else:
                logging.warning("⚠️ No se encontró correo en sessionStorage.")
        except Exception as e:
            logging.error(f"❌ Error al recuperar sessionStorage: {e}")

    def quit_driver(self):
        """
        Cierra y elimina el WebDriver manualmente.
        """
        if self.driver:
            try:
                self.driver.quit()
                logging.info("✅ WebDriver cerrado correctamente.")
            except Exception as e:
                logging.warning(f"⚠️ Error al cerrar el WebDriver: {e}")
            finally:
                self.driver = None

    def is_grid_ready(self, max_retries=5, wait_time=3):
        """
        Comprueba si Selenium Grid está listo antes de iniciar una sesión.
        Reintenta varias veces si no está listo.
        """
        for attempt in range(max_retries):
            try:
                logging.info(f"🔍 Verificando Selenium Grid (Intento {attempt + 1}/{max_retries}) en: {self.grid_url}")
                response = requests.get(f"{self.grid_url}/status", timeout=5)
                if response.status_code == 200 and response.json().get("value", {}).get("ready", False):
                    logging.info("✅ Selenium Grid está listo para aceptar conexiones.")
                    return True
                logging.warning(f"⚠️ Selenium Grid no está listo aún. Esperando {wait_time} segundos...")
                time.sleep(wait_time)
            except requests.RequestException as e:
                logging.error(f"❌ Error al verificar Selenium Grid: {e}")
                time.sleep(wait_time)
        logging.error("❌ Selenium Grid sigue sin estar listo. Abortando.")
        return False


def tomar_screenshot(driver, filename):
    """
    Captura una imagen de la pantalla y la guarda en la carpeta 'screenshots'.
    """
    try:
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)  # Crea la carpeta si no existe
        filepath = os.path.join(screenshots_dir, f"{filename}.png")
        driver.save_screenshot(filepath)
        logging.info(f"📸 Captura de pantalla guardada: {filepath}")
    except Exception as e:
        logging.error(f"❌ Error al tomar captura de pantalla: {e}")