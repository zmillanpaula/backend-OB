import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_manager import tomar_screenshot

def asignar_nivel_avanzado(driver, correo, nivel):
    """
    Asigna un nivel avanzado en Campus Virtual navegando desde el panel principal hasta la sección de Cohortes.
    """
    try:
        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}.")

        if not driver:
            raise Exception("❌ WebDriver no disponible.")

        # 🔹 Navegar desde el panel principal
        logging.info("🌍 Accediendo al panel principal...")
        driver.get("https://campusvirtual.bestwork.cl/my/")

        # 🔹 Acceder a Administración del sitio
        logging.info("📂 Accediendo a Administración del sitio...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Administración del sitio"))
        ).click()

        # 🔹 Ir a la pestaña Usuarios
        logging.info("👥 Cambiando a la sección Usuarios...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Usuarios"))
        ).click()

        # 🔹 Ir a Cohortes
        logging.info("📂 Accediendo a Cohortes...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Cohortes"))
        ).click()

        results = []

        for week in range(1, 13):  # 🔹 Iterar de Week 01 a Week 12
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

                cohort_icon = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
                )
                cohort_icon.click()

                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "addselect_searchtext"))
                )
                email_input.clear()
                email_input.send_keys(correo)

                # 🔹 Agregar tiempo de espera extra para cargar la lista de usuarios
                time.sleep(3)  # Espera 3 segundos antes de verificar si aparece el usuario

                user_select = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "addselect"))
                )
                optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
                label_text = optgroup.get_attribute("label")

                if "Ningún usuario coincide" in label_text:
                    logging.warning(f"⚠️ Usuario {correo} NO encontrado en {week_str}.")
                    tomar_screenshot(driver, f"usuario_no_encontrado_{week_str}")
                    results.append({"week": week_str, "result": "Usuario no encontrado"})
                else:
                    user_option = optgroup.find_element(By.TAG_NAME, "option")
                    user_option.click()

                    add_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "add"))
                    )
                    add_button.click()

                    logging.info(f"✅ Usuario {correo} asignado a {week_str}.")
                    results.append({"week": week_str, "result": "Asignación exitosa"})

            except Exception as e:
                logging.error(f"❌ Error en {week_str}: {e}")
                tomar_screenshot(driver, f"error_asignacion_{week_str}")
                results.append({"week": week_str, "result": f"Error: {str(e)}"})

            # 🔄 Volver a la página de "Cohortes" para la siguiente iteración
            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(3)

        logging.info("✅ Asignación avanzada completada.")

        return {"message": "✅ Asignación avanzada completada.", "details": results}

    except Exception as e:
        logging.error(f"❌ Error general en la asignación avanzada: {e}")
        tomar_screenshot(driver, "error_general_asignacion")
        return {"error": str(e)}

    finally:
        # 🔹 Cerrar el WebDriver al finalizar el proceso
        logging.info("🔚 Cerrando WebDriver después de completar la asignación.")
        driver.quit()