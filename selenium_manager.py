from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import logging
import requests
import os
import time


class SeleniumManager:
    def __init__(self, grid_url=None):
        self.driver = None
        self.grid_url = grid_url or os.environ.get("SELENIUM_GRID_URL", "http://localhost:4444/wd/hub")

    def start_driver(self):
        """
        Inicializa el WebDriver o reutiliza el existente.
        Si es necesario, hace login automáticamente.
        """
        if self.driver:
            try:
                self.driver.title  # Verifica si el WebDriver sigue activo
                logging.info("✅ WebDriver activo, reutilizando sesión.")
                return self.driver
            except Exception as e:
                logging.warning(f"⚠️ WebDriver no disponible. Reiniciando... {e}")
                self.driver = None

        # Verifica si Selenium Grid está disponible antes de iniciar el WebDriver
        if not self.is_grid_ready():
            raise Exception("❌ Selenium Grid no está listo.")

        try:
            options = Options()
            options.add_argument("--headless")  # Opcional: remover si necesitas ver el navegador
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")

            self.driver = webdriver.Remote(command_executor=self.grid_url, options=options)
            logging.info("🔄 WebDriver reiniciado.")

            # 🔹 Realizar login automático
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

            username = "189572484"
            password = "Mp18957248-4"

            WebDriverWait(self.driver, 10).until(
                lambda d: d.find_element(By.ID, "username")
            ).send_keys(username)
            self.driver.find_element(By.ID, "password").send_keys(password)
            self.driver.find_element(By.ID, "loginbtn").click()

            logging.info("✅ Login automático completado.")
        except Exception as e:
            logging.error(f"❌ Error durante el login: {e}")

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

    def is_grid_ready(self):
        """
        Comprueba si Selenium Grid está listo para recibir sesiones.
        """
        try:
            logging.info(f"🔍 Comprobando Selenium Grid en: {self.grid_url}")
            response = requests.get(f"{self.grid_url}/status", timeout=5)
            if response.status_code == 200 and response.json().get("value", {}).get("ready", False):
                logging.info("✅ Selenium Grid está listo.")
                return True
            logging.warning(f"⚠️ Selenium Grid no está listo: {response.text}")
            return False
        except requests.RequestException as e:
            logging.error(f"❌ Error al verificar Selenium Grid: {e}")
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