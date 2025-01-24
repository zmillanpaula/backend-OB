import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

def asignar_nivel_campus(driver, correo, nivel):
    try:
        logging.info("Navegando a Cohortes")
        driver.get("https://campusvirtual.bestwork.cl/cohort/index.php")

        # Buscar el nivel
        logging.info(f"Buscando el nivel '{nivel}'")
        search_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='search']"))
        )
        search_input.send_keys(nivel)

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.btn-submit.search-icon"))
        )
        search_button.click()

        logging.info("Nivel buscado, seleccionando...")
        cohort_icon = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "i.icon.fa.fa-users"))
        )
        cohort_icon.click()

        # Buscar en la lista de usuarios potenciales
        logging.info("Buscando el correo en el campo de usuarios potenciales...")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "addselect_searchtext"))
        )
        email_input.send_keys(correo)
        time.sleep(2)  # Dar tiempo para cargar la lista

        user_select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "addselect"))
        )

        optgroup = user_select.find_element(By.TAG_NAME, "optgroup")
        label_text = optgroup.get_attribute("label")

        if "Ningún usuario coincide" in label_text:
            logging.warning(f"No se encontró el usuario con correo {correo} en la lista de usuarios potenciales. Verificando usuarios existentes.")

            # Buscar en la lista de usuarios existentes
            logging.info("Buscando el correo en la lista de usuarios existentes...")
            existing_email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "removeselect_searchtext"))
            )
            existing_email_input.send_keys(correo)
            time.sleep(2)  # Dar tiempo para cargar la lista

            existing_user_select = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "removeselect"))
            )
            existing_optgroup = existing_user_select.find_element(By.TAG_NAME, "optgroup")
            existing_label_text = existing_optgroup.get_attribute("label")

            if "Ningún usuario coincide" in existing_label_text:
                logging.warning(f"No se encontró el usuario con correo {correo} en usuarios existentes tampoco.")
                return {"error": f"El usuario con correo {correo} no fue encontrado en ninguna lista."}
            else:
                logging.info(f"El usuario con correo {correo} ya está asignado al nivel.")
                return {"message": f"El usuario con correo {correo} ya está asignado al nivel '{nivel}'."}
        else:
            # Si el usuario está en la lista de usuarios potenciales
            logging.info("Seleccionando usuario encontrado en usuarios potenciales...")
            user_option = optgroup.find_element(By.TAG_NAME, "option")
            user_option.click()

            # Presionar Añadir
            logging.info("Añadiendo usuario al nivel...")
            add_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "add"))
            )
            add_button.click()

            return {"message": f"Nivel '{nivel}' asignado exitosamente al estudiante con correo {correo}."}

    except Exception as e:
        logging.error(f"Error en la asignación de nivel: {e}")
        return {"error": str(e)}