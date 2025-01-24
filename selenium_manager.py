import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import time


class SeleniumManager:
    def __init__(self, grid_url="http://selenium:4444/wd/hub"):
        self.driver = None
        self.grid_url = grid_url

    def start_driver(self):
        """
        Inicializa el WebDriver si no está activo.
        """
        if self.driver:
            logging.info("WebDriver ya está activo.")
            return self.driver

        if not self.is_grid_ready():
            raise Exception("Selenium Grid no está listo.")

        try:
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            self.driver = webdriver.Remote(
                command_executor=self.grid_url,
                options=options,
            )
            logging.info("WebDriver inicializado correctamente.")
        except Exception as e:
            logging.error(f"Error al iniciar el WebDriver: {e}")
            raise

    def reset_session(self):
        """
        Cierra el WebDriver y elimina la sesión activa.
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
            response = requests.get(f"{self.grid_url}/status", timeout=5)
            if response.status_code == 200:
                ready = response.json().get("value", {}).get("ready", False)
                logging.info(f"Selenium Grid listo: {ready}")
                return ready
            logging.warning(f"Estado del Grid desconocido: {response.text}")
            return False
        except requests.RequestException as e:
            logging.error(f"Error al verificar Selenium Grid: {e}")
            return False

    def run(self, operation):
        """
        Ejecuta una operación con el WebDriver.
        """
        try:
            self.start_driver()
            return operation(self.driver)
        except Exception as e:
            logging.error(f"Error durante la operación Selenium: {e}")
            raise
        finally:
            self.reset_session()