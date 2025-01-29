import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
from activeCampaignService import get_contact

def asignar_nivel_avanzado(driver, nivel):
    try:
        # Recuperar correo almacenado en sessionStorage
        logging.info("Obteniendo correo del estudiante desde sessionStorage.")
        correo = driver.execute_script("return sessionStorage.getItem('correo_estudiante');")
        if not correo:
            raise ValueError("No se encontró el correo en sessionStorage. Verifica el flujo de búsqueda.")

        logging.info(f"Correo recuperado: {correo}")

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
                logging.error(f"Error asignando '{week_str}': {e}")
                results.append({"week": week_str, "result": f"Error: {str(e)}"})

            # Navegar de vuelta a "Cohortes"
            driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")
            time.sleep(2)

        return {"message": "Asignación avanzada completada.", "details": results}

    except Exception as e:
        logging.error(f"Error en la asignación de nivel avanzado: {e}")
        return {"error": str(e)}

    