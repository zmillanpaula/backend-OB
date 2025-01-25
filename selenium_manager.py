from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import requests


class SeleniumManager:
    def __init__(self, grid_url="http://localhost:4444/wd/hub"):
        self.driver = None
        self.grid_url = grid_url

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

    def start_driver(self):
        """
        Inicializa el WebDriver si el Grid está listo.
        """
        if self.driver:
            logging.info("WebDriver ya está activo.")
            return self.driver

        if not self.is_grid_ready():
            raise Exception("Selenium Grid no está listo.")

        try:
            options = Options()
            options.add_argument("--headless")
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
        Cierra y elimina el WebDriver.
        """
        if self.driver:
            try:
                self.driver.quit()
                logging.info("WebDriver cerrado correctamente.")
            except Exception as e:
                logging.warning(f"Error al cerrar el WebDriver: {e}")
            finally:
                self.driver = None

    def run(self, operation):
        """
        Ejecuta una operación con el WebDriver.
        """
        try:
            # Inicializa el driver si no está activo
            driver = self.start_driver()
            return operation(driver)
        except Exception as e:
            logging.error(f"Error durante la operación Selenium: {e}")
            raise
        finally:
            # Cierra el driver al final de la operación
            self.quit_driver()