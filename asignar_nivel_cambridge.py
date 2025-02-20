import time
import re
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from activeCampaignService import get_contact

# Función para transformar el nivel ingresado
def transformar_nivel(nivel):
    niveles_dict = {
        "3A": "3A LOWER INTERMEDIATE (N5)",
        "4A": "4A UPPER INTERMEDIATE (N7)",
        "5A": "5A ADVANCED I (N9)"
    }
    return niveles_dict.get(nivel, nivel)

def invitacion_cambridge(driver, correo, nivel_ingresado):
    """
    Función para enviar una invitación en la plataforma Cambridge y extraer la classKey.
    """
    class_key = None

    try:
        driver.get("https://www.cambridgeone.org/admin/admin/org_bestworkvirtual-chile-prod1/learner")
        logging.info("🌐 Accediendo a Cambridge One...")

        # Ingresar usuario
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="gigya-loginID-56269462240752180"]'))
        )
        username_field.send_keys("activacionlicencia@bestwork.cl")

        # Ingresar contraseña
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="gigya-password-56383998600152700"]'))
        )
        password_field.send_keys("Bestwork2021")

        # Clic en el botón de login
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="gigya-login-form"]/div[2]/div[1]/input'))
        )
        actions = ActionChains(driver)
        actions.move_to_element(login_button).click().perform()
        logging.info("✅ Inicio de sesión exitoso.")

        # Intentar hacer clic en "Take me back home" si aparece
        try:
            back_home_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Take me back home")]'))
            )
            back_home_button.click()
            logging.info("✅ Botón 'Take me back home' encontrado y clickeado.")
        except Exception:
            logging.info("🔍 No se encontró el botón 'Take me back home', continuando...")

        time.sleep(4)  # Esperar a que cargue el dashboard

        # Buscar el curso correspondiente
        nivel_transformado = transformar_nivel(nivel_ingresado)
        nivel_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="classNameSearch"]'))
        )
        nivel_input.clear()
        nivel_input.send_keys(nivel_transformado)

        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@qid="aClass-2"]'))
        )
        search_button.click()

        time.sleep(3)  # Esperar a que cargue la lista

        cursos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "list-items")]//a[contains(@class, "class-details")]'))
        )

        # Seleccionar el curso con el paralelo más alto
        curso_nombres = [curso.text for curso in cursos if nivel_transformado in curso.text and "Progress Reset Class" not in curso.text]

        paralelo_max = 0
        curso_final = None
        for curso in curso_nombres:
            match = re.search(r"(\d+)$", curso)
            if match:
                num_paralelo = int(match.group(1))
                if num_paralelo > paralelo_max:
                    paralelo_max = num_paralelo
                    curso_final = curso

        if curso_final:
            curso_elemento = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//a[text()="{curso_final}"]'))
            )
            curso_elemento.click()

            time.sleep(2)

            add_students_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@qid="cView-73"]'))
            )
            add_students_button.click()

            time.sleep(2)

            # Selección de tipo de estudiante
            adult_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//label[@for="adult-radio"]'))
            )
            adult_option.click()

            time.sleep(1)
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@qid="typeSelect-4"]'))
            )
            next_button.click()

            time.sleep(2)

            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="email"]'))
            )
            email_input.clear()
            email_input.send_keys(correo)

            contacto = get_contact(correo)
            if contacto:
                first_name = contacto.get("firstName", "").strip()
                last_name = contacto.get("lastName", "").strip()

                first_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="firstName"]'))
                )
                first_name_input.clear()
                first_name_input.send_keys(first_name)

                last_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="lastName"]'))
                )
                last_name_input.clear()
                last_name_input.send_keys(last_name)

            time.sleep(1)

            invite_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@qid="CBulkEnrollment-4"]'))
            )
            invite_button.click()

            time.sleep(2)

            class_key_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//p[contains(@class, "class-key")]/strong'))
            )
            class_key = class_key_element.text
            logging.info(f"🔑 **Class Key extraída:** {class_key}")

        else:
            return {"error": "No se encontraron cursos disponibles"}

    except Exception as e:
        logging.error(f"❌ Error en la invitación de Cambridge: {e}")
        return {"error": str(e)}

    return {"success": True, "classKey": class_key}