import time
import re
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Importamos la función para obtener datos desde ActiveCampaign
from activeCampaignService import get_contact

# Función para transformar el nivel ingresado
def transformar_nivel(nivel):
    niveles_dict = {
        "3A": "3A LOWER INTERMEDIATE (N5)",
        "4A": "4A UPPER INTERMEDIATE (N7)",
        "5A": "5A ADVANCED I (N9)"
    }
    return niveles_dict.get(nivel, nivel)  # Si no está en el diccionario, devuelve el mismo valor

def login_cambridge(nivel_ingresado, email):
    driver = webdriver.Chrome()

    try:
        driver.get("https://www.cambridgeone.org/admin/admin/org_bestworkvirtual-chile-prod1/learner")

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

        print("Inicio de sesión exitoso.")

        # Esperar hasta 5 segundos para ver si aparece el botón "Take me back home"
        try:
            back_home_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Take me back home")]'))
            )
            back_home_button.click()
            print("Botón 'Take me back home' encontrado y clickeado.")
        except Exception:
            print("No se encontró el botón 'Take me back home', continuando...")

        # Esperar 4 segundos para el dashboard
        time.sleep(4)

        # Buscar el campo de búsqueda de nivel
        nivel_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="classNameSearch"]'))
        )

        # Limpiar el campo antes de ingresar el nivel
        nivel_input.clear()

        # Transformar el nivel ingresado y escribirlo en el input
        nivel_transformado = transformar_nivel(nivel_ingresado)
        nivel_input.send_keys(nivel_transformado)
        print(f"Nivel ingresado: {nivel_transformado}")

        # Clic en el botón "Search"
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[@qid="aClass-2"]'))
        )
        search_button.click()
        print("Botón 'Search' clickeado.")

        # Esperar a que carguen los resultados
        time.sleep(3)

        # Obtener la lista de cursos disponibles
        cursos = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.XPATH, '//div[contains(@class, "list-items")]//a[contains(@class, "class-details")]'))
        )

        # Filtrar los cursos válidos (excluir "Progress Reset Class")
        curso_nombres = [curso.text for curso in cursos if nivel_transformado in curso.text and "Progress Reset Class" not in curso.text]

        # Buscar el paralelo más alto
        paralelo_max = 0
        curso_final = None
        for curso in curso_nombres:
            match = re.search(r"(\d+)$", curso)  # Buscar número al final del nombre
            if match:
                num_paralelo = int(match.group(1))
                if num_paralelo > paralelo_max:
                    paralelo_max = num_paralelo
                    curso_final = curso

        if curso_final:
            print(f"\n✅ Seleccionando el último curso disponible: {curso_final}")

            # Hacer clic en el curso correspondiente
            curso_elemento = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f'//a[text()="{curso_final}"]'))
            )
            curso_elemento.click()
            print("✅ Curso seleccionado correctamente.")

            # Esperar 2 segundos para que cargue la nueva interfaz
            time.sleep(2)

            # Clic en "Add students"
            add_students_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[@qid="cView-73"]'))
            )
            add_students_button.click()
            print("✅ Botón 'Add students' clickeado.")

            # Esperar 2 segundos para que cargue la pantalla de selección
            time.sleep(2)

            # Clic en "Adults"
            adult_option = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//label[@for="adult-radio"]'))
            )
            adult_option.click()
            print("✅ Opción 'Adults' seleccionada.")

            # Esperar 1 segundo y hacer clic en "Next"
            time.sleep(1)
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@qid="typeSelect-4"]'))
            )
            next_button.click()
            print("✅ Botón 'Next' clickeado.")

            # Esperar 2 segundos antes de ingresar los datos
            time.sleep(2)

            # Ingresar el correo en el campo de email
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="email"]'))
            )
            email_input.clear()
            email_input.send_keys(email)
            print(f"✅ Correo {email} ingresado correctamente.")

            # Obtener datos desde ActiveCampaign
            contacto = get_contact(email)

            if contacto:
                first_name = contacto.get("firstName", "").strip()
                last_name = contacto.get("lastName", "").strip()

                # Ingresar el nombre
                first_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="firstName"]'))
                )
                first_name_input.clear()
                first_name_input.send_keys(first_name)
                print(f"✅ Nombre ingresado: {first_name}")

                # Ingresar el apellido
                last_name_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//input[@formcontrolname="lastName"]'))
                )
                last_name_input.clear()
                last_name_input.send_keys(last_name)
                print(f"✅ Apellido ingresado: {last_name}")

            # Esperar 1 segundo antes de invitar al estudiante
            time.sleep(1)

            # Hacer clic en "Invite 1 student"
            invite_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@qid="CBulkEnrollment-4"]'))
            )
            invite_button.click()
            print("✅ Botón 'Invite 1 student' clickeado.")

            # Esperar 2 segundos antes de extraer la "Class key"
            time.sleep(2)

            # Extraer la "Class key"
            class_key_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//p[contains(@class, "class-key")]/strong'))
            )
            class_key = class_key_element.text
            print(f"\n🔑 **Class Key extraída:** {class_key}")

        else:
            print("⚠️ No se encontraron cursos disponibles.")

        input("Presiona Enter para cerrar el navegador...")

    except Exception as e:
        print(f"\n❌ Error durante el proceso: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    email_usuario = input("Ingrese el correo del estudiante: ").strip().lower()
    nivel_usuario = input("Ingrese el nivel (ej. 3A, 4A, 5A): ").strip().upper()
    login_cambridge(nivel_usuario, email_usuario)