import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from selenium_manager import tomar_screenshot
import selenium_manager  # Para reiniciar el driver si se pierde la sesión


def asignar_nivel_avanzado(driver, correo, nivel):
    """
    Asigna un estudiante a todos los niveles avanzados (Week 01 a Week 12) en Campus Virtual.
    """
    try:
        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}.")

        # 🔹 Navegar a la página de Cohortes
        logging.info("🔄 Navegando a 'Cohortes'")
        driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")

        resultados = []

        for week in range(1, 13):  # 🔹 Iterar de "Week 01" a "Week 12"
            week_str = f"{nivel} Week {week:02d}"
            logging.info(f"🔎 Buscando nivel: {week_str}")

            # 📌 Verificar si el WebDriver sigue activo
            try:
                driver.current_window_handle  # Si falla, significa que la sesión está perdida
            except:
                logging.warning("⚠️ Sesión de Selenium perdida. Reiniciando WebDriver...")
                driver = selenium_manager.start_driver()  # 🔄 Reiniciar WebDriver y mantener login activo

            try:
                # 🔹 Buscar el nivel
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='search']"))
                )
                search_input.clear()
                search_input.send_keys(week_str)

                search_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-submit.search-icon"))
                )
                search_button.click()

                # Esperar a que aparezca el icono de usuarios y seleccionarlo
                cohort_icon = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
                )
                cohort_icon.click()

                # 🔎 Buscar al estudiante en la lista de usuarios potenciales
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "addselect_searchtext"))
                )
                email_input.clear()
                email_input.send_keys(correo)

                time.sleep(2)  # Pequeño delay para actualizar la lista

                # Verificar si hay resultados en la lista de usuarios potenciales
                user_select = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "addselect"))
                )
                optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
                label_text = optgroup.get_attribute("label")

                if "Ningún usuario coincide" in label_text:
                    logging.warning(f"❌ No se encontró el usuario {correo} en {week_str}")
                    tomar_screenshot(driver, f"usuario_no_encontrado_{week_str}")
                    resultados.append({"week": week_str, "result": "Usuario no encontrado"})
                else:
                    # 🔹 Seleccionar usuario y añadirlo al curso
                    user_option = optgroup.find_element(By.TAG_NAME, "option")
                    user_option.click()

                    add_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "add"))
                    )
                    add_button.click()

                    logging.info(f"✅ Usuario {correo} asignado a {week_str}.")
                    resultados.append({"week": week_str, "result": "Asignación exitosa"})

            except Exception as e:
                logging.error(f"❌ Error asignando '{week_str}': {e}")
                tomar_screenshot(driver, f"error_asignacion_{week_str}")
                resultados.append({"week": week_str, "result": f"Error: {str(e)}"})

            # 🔄 Volver a la página de Cohortes antes de la siguiente iteración
            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(2)

        return {"message": "✅ Asignación avanzada completada.", "details": resultados}

    except Exception as e:
        logging.error(f"❌ Error general en la asignación avanzada: {e}")
        tomar_screenshot(driver, "error_general_asignacion")
        return {"error": str(e)}