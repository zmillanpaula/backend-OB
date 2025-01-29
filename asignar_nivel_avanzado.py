import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from app.selenium_manager import tomar_screenshot  # 🔹 Importamos la función desde selenium_manager.py

def asignar_nivel_avanzado(driver, correo, nivel):
    """
    Asigna un nivel avanzado a un estudiante en Campus Virtual.
    """
    try:
        logging.info(f"Iniciando asignación avanzada para {correo} en nivel {nivel}.")

        # Navegar a "Cohortes"
        logging.info("Navegando a 'Cohortes'")
        driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")

        results = []
        for week in range(1, 13):  # Iterar de Week 01 a Week 12
            week_str = f"{nivel} Week {week:02d}"
            logging.info(f"Buscando el nivel '{week_str}'")

            try:
                # Buscar el nivel
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='search']"))
                )
                search_input.clear()
                search_input.send_keys(week_str)

                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-submit.search-icon"))
                )
                search_button.click()

                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
                )

                # Seleccionar el primer resultado
                first_result_icon = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
                )
                first_result_icon.click()

                # Buscar al estudiante y asignarlo
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "addselect_searchtext"))
                )
                email_input.clear()
                email_input.send_keys(correo)

                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.ID, "addselect"))
                )
                user_select = driver.find_element(By.ID, "addselect")
                optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
                label_text = optgroup.get_attribute("label")

                if "Ningún usuario coincide" in label_text:
                    logging.warning(f"No se encontró el usuario con correo {correo} en '{week_str}'")
                    tomar_screenshot(driver, f"usuario_no_encontrado_{week_str}")  # 🔹 Captura en caso de error
                    results.append({"week": week_str, "result": "Usuario no encontrado"})
                else:
                    user_option = optgroup.find_element(By.TAG_NAME, "option")
                    user_option.click()

                    add_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "add"))
                    )
                    add_button.click()

                    results.append({"week": week_str, "result": "Asignación exitosa"})
            except Exception as e:
                logging.error(f"❌ Error asignando '{week_str}': {e}")
                tomar_screenshot(driver, f"error_asignacion_{week_str}")  # 🔹 Captura en caso de error
                results.append({"week": week_str, "result": f"Error: {str(e)}"})

            # Navegar de vuelta a "Cohortes"
            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(2)

        return {"message": "Asignación avanzada completada.", "details": results}

    except Exception as e:
        logging.error(f"❌ Error en la asignación de nivel avanzado: {e}")
        tomar_screenshot(driver, "error_general_asignacion")  # 🔹 Captura en caso de error general
        return {"error": str(e)}