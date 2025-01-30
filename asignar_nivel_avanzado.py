import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_manager import tomar_screenshot
import selenium_manager

def asignar_nivel_avanzado(driver, correo, nivel):
    """
    Asigna un nivel avanzado a un estudiante en Campus Virtual en grupos de 3 semanas.
    """
    try:
        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}.")

        # Verificar si la sesión de Selenium sigue activa
        try:
            driver.current_window_handle  # Intenta acceder a la sesión actual
        except:
            logging.warning("⚠️ Sesión de Selenium perdida. Reiniciando WebDriver...")
            driver = selenium_manager.start_driver()  # Reinicia el driver

        # Navegar a "Cohortes"
        logging.info("🔄 Navegando a 'Cohortes'")
        driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
        time.sleep(2)  # Espera para evitar problemas de carga

        results = []

        # Procesar las semanas en grupos de 3
        for i in range(0, 12, 3):  # Secciones de 3 semanas (0-2, 3-5, ..., 9-11)
            for week in range(i + 1, i + 4):
                if week > 12:
                    break  # Evitar desbordamiento si hay menos de 3 semanas restantes

                week_str = f"{nivel} Week {week:02d}"
                logging.info(f"🔎 Buscando nivel: {week_str}")

                try:
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='search']"))
                    )
                    search_input.clear()
                    search_input.send_keys(week_str)

                    search_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-submit.search-icon"))
                    )
                    search_button.click()
                    time.sleep(2)  # Espera para que los resultados se carguen

                    # Verificar si el icono de usuarios aparece
                    cohort_icon = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
                    )
                    cohort_icon.click()

                    # Buscar en la lista de usuarios potenciales
                    logging.info("📌 Buscando el correo en usuarios potenciales...")
                    email_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "addselect_searchtext"))
                    )
                    email_input.clear()
                    email_input.send_keys(correo)

                    time.sleep(2)  # Espera para que los resultados se carguen

                    user_select = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "addselect"))
                    )

                    optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
                    label_text = optgroup.get_attribute("label")

                    if "Ningún usuario coincide" in label_text:
                        logging.warning(f"⚠️ No se encontró {correo} en '{week_str}'.")
                        tomar_screenshot(driver, f"usuario_no_encontrado_{week_str}")
                        results.append({"week": week_str, "result": "Usuario no encontrado"})
                    else:
                        # Seleccionar usuario y asignarlo
                        logging.info(f"✅ Usuario encontrado, asignando a {week_str}.")
                        user_option = optgroup.find_element(By.TAG_NAME, "option")
                        user_option.click()

                        add_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.ID, "add"))
                        )
                        add_button.click()

                        logging.info(f"✅ Usuario {correo} asignado a {week_str}.")
                        results.append({"week": week_str, "result": "Asignación exitosa"})

                except Exception as e:
                    logging.error(f"❌ Error asignando '{week_str}': {e}")
                    tomar_screenshot(driver, f"error_asignacion_{week_str}")
                    results.append({"week": week_str, "result": f"Error: {str(e)}"})

            # 🚀 Después de cada bloque de 3 semanas, validar sesión de Selenium y recargar Cohortes
            logging.info("🔄 Validando sesión de Selenium y recargando Cohortes...")
            try:
                driver.current_window_handle
            except:
                logging.warning("⚠️ Sesión perdida, reiniciando WebDriver...")
                driver = selenium_manager.start_driver()

            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(3)  # Esperar para asegurar carga

        return {"message": "Asignación avanzada completada.", "details": results}

    except Exception as e:
        logging.error(f"❌ Error general en la asignación avanzada: {e}")
        tomar_screenshot(driver, "error_general_asignacion")
        return {"error": str(e)}