import time
import logging
from flask import Response
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sse_manager import enviar_evento_sse


def asignar_nivel_avanzado(driver, correo, nivel):
    """
    Asigna un nivel avanzado en Campus Virtual navegando desde el panel principal hasta la sección de Cohortes.
    """
    try:
        logging.info(f"📌 Iniciando asignación avanzada para {correo} en nivel {nivel}.")
        enviar_evento_sse(correo, f"📌 Iniciando asignación avanzada para {correo}.")

        if not driver:
            raise Exception("❌ WebDriver no disponible.")

        # 🔹 Navegar desde el panel principal
        logging.info("🌍 Accediendo a Campus Virtual...")
        enviar_evento_sse(correo, "🌍 Accediendo a Campus Virtual...")
        driver.get("https://campusvirtual.bestwork.cl/my/")

        # 🔹 Acceder a Administración del sitio
        logging.info("📂 Accediendo a Administración del sitio...")
        enviar_evento_sse(correo, "📂 Accediendo a Administración del sitio...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Administración del sitio"))
        ).click()

        # 🔹 Ir a la pestaña Usuarios
        logging.info("👥 Cambiando a la sección Usuarios...")
        enviar_evento_sse(correo, "👥 Cambiando a la sección Usuarios...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Usuarios"))
        ).click()

        # 🔹 Ir a Cohortes
        logging.info("📂 Accediendo a Cohortes...")
        enviar_evento_sse(correo, "📂 Accediendo a Cohortes...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Cohortes"))
        ).click()

        results = []

        for week in range(1, 13):  # 🔹 Iterar de Week 01 a Week 12
            week_str = f"{nivel} Week {week:02d}"
            logging.info(f"🔎 Buscando nivel: {week_str}")
            enviar_evento_sse(correo, f"🔎 Buscando nivel: {week_str}")

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

                time.sleep(2)  # 🔹 Dar tiempo para cargar la lista

                user_select = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "addselect"))
                )
                optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
                label_text = optgroup.get_attribute("label")

                if "Ningún usuario coincide" in label_text:
                    logging.warning(f"⚠️ Usuario {correo} NO encontrado en {week_str}.")
                    enviar_evento_sse(correo, f"⚠️ Usuario NO encontrado en {week_str}.")
                    results.append({"week": week_str, "result": "Usuario no encontrado"})
                else:
                    user_option = optgroup.find_element(By.TAG_NAME, "option")
                    user_option.click()

                    add_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.ID, "add"))
                    )
                    add_button.click()

                    logging.info(f"✅ Usuario {correo} asignado a {week_str}.")
                    enviar_evento_sse(correo, f"✅ Usuario asignado a {week_str}.")
                    results.append({"week": week_str, "result": "Asignación exitosa"})

            except Exception as e:
                logging.error(f"❌ Error en {week_str}: {e}")
                enviar_evento_sse(correo, f"❌ Error en {week_str}: {e}")
                results.append({"week": week_str, "result": f"Error: {str(e)}"})

            # 🔄 Volver a la página de "Cohortes" para la siguiente iteración
            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(3)

        logging.info("✅ Asignación avanzada completada.")
        enviar_evento_sse(correo, "✅ Asignación avanzada completada.")
        return {"message": "✅ Asignación avanzada completada.", "details": results}

    except Exception as e:
        logging.error(f"❌ Error general en la asignación avanzada: {e}")
        enviar_evento_sse(correo, f"❌ Error: {str(e)}")
        return {"error": str(e)}
    
    finally:
        logging.info("Cerrando webdriver")
        driver.quit()