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

        

def asignar_estudiante_cambridge(driver, nivel):
    """
    Asigna un estudiante a un curso en Cambridge LMS, manejando cursos enumerados si es necesario.
    """
    try:
        # Recuperar correo almacenado en sessionStorage
        logging.info("Obteniendo correo del estudiante desde sessionStorage.")
        correo = driver.execute_script("return sessionStorage.getItem('correo_estudiante');")
        if not correo:
            raise ValueError("No se encontró el correo en sessionStorage. Verifica el flujo de búsqueda.")

        logging.info(f"Correo recuperado: {correo}")

        # Transformar el nivel para búsqueda en Cambridge
        niveles_transformados = {
            "3A": "3A LOWER INTERMEDIATE (N5)",
            "4A": "4A UPPER INTERMEDIATE (N7)",
            "5A": "5A ADVANCED I (N9)",
            "6A": "6A PROFICIENT (11)"
        }
        curso_base = niveles_transformados.get(nivel)
        if not curso_base:
            raise ValueError(f"Nivel '{nivel}' no reconocido.")

        logging.info(f"Nivel transformado para Cambridge: {curso_base}")

        # Navegar a Cambridge LMS e iniciar sesión
        logging.info("Accediendo a Cambridge LMS.")
        driver.get("https://www.cambridgeone.org/login")

        logging.info("Iniciando sesión en Cambridge LMS.")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys("activacionlicencia@bestwork.cl")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        ).send_keys("Bestwork2021")

        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "input.gigya-input-submit"))
        ).click()

        # Cambiar a vista Teacher
        logging.info("Cambiando a vista Teacher.")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[data-checked='Teacher']"))
        ).click()

        # Navegar a la lista de cursos
        logging.info("Navegando a la lista de cursos en Cambridge.")
        driver.get("https://www.cambridgeone.org/dashboard/teacher/dashboard")

        results = []
        numero_curso = 1
        curso_asignado = None

        while not curso_asignado:
            # Construir el nombre del curso con el número
            curso_actual = curso_base if numero_curso == 1 else f"{curso_base} {numero_curso}"
            logging.info(f"Buscando curso: {curso_actual}")

            # Buscar el curso en la lista
            course_links = driver.find_elements(By.CSS_SELECTOR, "a.class-title")
            curso_encontrado = None
            for link in course_links:
                if curso_actual in link.text:
                    logging.info(f"Curso encontrado: {link.text}")
                    curso_encontrado = link
                    break

            if not curso_encontrado:
                logging.error(f"No se encontró un curso disponible para '{curso_base}'.")
                results.append({"course": curso_actual, "result": "No encontrado"})
                return {"message": "No se encontraron cursos disponibles.", "details": results}

            # Seleccionar el curso
            curso_encontrado.click()

            # Verificar cantidad de estudiantes
            logging.info("Verificando cantidad de estudiantes en el curso.")
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button.accordion-button"))
                ).click()

                student_count_element = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.student-count"))
                )
                student_count = int(student_count_element.text.split()[0])  # Extraer número de estudiantes

                if student_count < 95:
                    logging.info(f"Curso '{curso_actual}' tiene {student_count} estudiantes. Asignando...")
                    curso_asignado = curso_actual
                else:
                    logging.warning(f"Curso '{curso_actual}' tiene {student_count} estudiantes. Probando el siguiente.")
                    driver.back()
                    numero_curso += 1
            except Exception as e:
                logging.error(f"Error al verificar el curso: {e}")
                driver.back()
                numero_curso += 1

        # Añadir estudiante al curso
        logging.info(f"Añadiendo estudiante '{correo}' al curso '{curso_asignado}'.")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.add-button"))
        ).click()

        # Completar datos del estudiante
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#email-0"))
        ).send_keys(correo)

        # Consultar ActiveCampaign para nombre y apellidos
        contacto = get_contact(correo)
        if not contacto:
            raise ValueError(f"No se encontró información para el correo {correo} en ActiveCampaign.")

        nombre = contacto.get("firstName", "DefaultName")
        apellidos = contacto.get("lastName", "DefaultLastName")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#firstName-0"))
        ).send_keys(nombre)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#lastName-0"))
        ).send_keys(apellidos)

        # Enviar invitación
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.save-btn"))
        ).click()

        logging.info(f"Estudiante añadido exitosamente al curso '{curso_asignado}'.")
        return {"message": f"Estudiante añadido exitosamente al curso '{curso_asignado}'.", "course": curso_asignado}

    except Exception as e:
        logging.error(f"Error en la asignación de estudiante: {e}")
        return {"error": str(e)}

    finally:
        driver.quit()