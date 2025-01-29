from selenium import webdriver
from selenium.webdriver.chrome.options import Options
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
        """
        if self.driver:
            try:
                # Verifica si el driver sigue vivo
                self.driver.title  # Una operación sencilla para validar el estado
                logging.info("WebDriver está activo y reutilizable.")
                return self.driver
            except Exception as e:
                logging.warning(f"WebDriver no está disponible. Reiniciando: {e}")
                self.driver = None

        # Si el driver no está inicializado, verifica si Selenium Grid está listo
        if not self.is_grid_ready():
            raise Exception("Selenium Grid no está listo.")

        try:
            options = Options()
            options.add_argument("--headless")  # Opcional: Remover si necesitas ver el navegador
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Remote(
                command_executor=self.grid_url,
                options=options
            )
            logging.info("WebDriver inicializado correctamente.")
            return self.driver
        except Exception as e:
            logging.error(f"Error al iniciar el WebDriver: {e}")
            raise

    def quit_driver(self):
        """
        Cierra y elimina el WebDriver manualmente.
        """
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver cerrado correctamente.")
            except Exception as e:
                logging.warning(f"Error al cerrar el WebDriver: {e}")
            finally:
                self.driver = None

    def is_grid_ready(self):
        """
        Comprueba si Selenium Grid está listo para recibir sesiones.
        """
        try:
            logging.info(f"Comprobando Selenium Grid en: {self.grid_url}")
            response = requests.get(f"{self.grid_url}/status", timeout=5)
            if response.status_code == 200 and response.json().get("value", {}).get("ready", False):
                logging.info("Selenium Grid está listo.")
                return True
            logging.warning(f"Selenium Grid no está listo: {response.text}")
            return False
        except requests.RequestException as e:
            logging.error(f"Error al verificar Selenium Grid: {e}")
            return False
        
def tomar_screenshot(driver, filename):
    """
    Captura una captura de pantalla y la guarda en la carpeta 'screenshots'.
    """
    try:
        screenshots_dir = "screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)  # Crea la carpeta si no existe
        filepath = os.path.join(screenshots_dir, f"{filename}.png")
        driver.save_screenshot(filepath)
        logging.info(f"✅ Captura de pantalla guardada: {filepath}")
    except Exception as e:
        logging.error(f"❌ Error al tomar captura de pantalla: {e}")