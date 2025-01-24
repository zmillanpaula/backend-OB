import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from activeCampaignService import get_contact

def obtener_monitores():
    """
    Obtiene la lista de monitores (campo personalizado con ID 149) desde ActiveCampaign.
    """
    logging.info("Consultando monitores desde ActiveCampaign.")
    
    # ID del campo personalizado de monitores
    campo_monitor_id = "149"
    monitores = []
    
    try:
        # Consulta un contacto genérico para obtener la lista de monitores
        contacto = get_contact("dummy@example.com")  # Puedes ajustar el email si es necesario
        
        if not contacto or not contacto.get("fieldValues"):
            logging.warning("No se encontraron contactos o valores personalizados para los monitores.")
            return []

        # Extraer valores únicos del campo de monitores
        monitores = set()
        for field in contacto.get("fieldValues", []):
            if field.get("field") == campo_monitor_id:
                monitores.add(field.get("value", "").strip())

        logging.info(f"Monitores encontrados: {monitores}")
        return list(monitores)

    except Exception as e:
        logging.error(f"Error al obtener monitores desde ActiveCampaign: {e}")
        return []

def login_y_buscar_estudiante(driver, admin_username, password, correo):
    try:
        logging.info("Iniciando SeleniumManager para mantener la sesión activa")

        # Paso 1: Navegar al login
        logging.info("Navegando a la página de login")
        driver.get("https://campusvirtual.bestwork.cl/login/index.php")

        # Paso 2: Ingresar credenciales
        logging.info("Ingresando credenciales")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        username_field.clear()
        username_field.send_keys(admin_username)

        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        password_field.clear()
        password_field.send_keys(password)

        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "loginbtn"))
        )
        login_button.click()

        # Paso 3: Verificar inicio de sesión exitoso
        logging.info("Verificando el inicio de sesión")
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//img[contains(@src, 'Bienvenido')]"))
            )
            logging.info("Inicio de sesión exitoso.")
        except Exception:
            logging.error("Error en el inicio de sesión. Verifica las credenciales.")
            return {"error": "Credenciales inválidas", "existe": False}

        # Paso 4: Navegar a Administración del sitio
        logging.info("Navegando a Administración del sitio")
        driver.get("https://campusvirtual.bestwork.cl/admin/search.php")

        # Paso 5: Presionar Usuarios
        logging.info("Presionando Usuarios")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Usuarios"))
        ).click()

        # Paso 6: Presionar Mirar lista de usuarios
        logging.info("Presionando Mirar lista de usuarios")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@href='https://campusvirtual.bestwork.cl/admin/user.php']"))
        ).click()

        # Paso 7: Mostrar más opciones de búsqueda
        logging.info("Mostrando más opciones de búsqueda")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Mostrar más..."))
        ).click()

        # Paso 8: Ingresar correo del estudiante
        logging.info(f"Ingresando correo del estudiante: {correo}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_email"))
        ).send_keys(correo)

        # Paso 9: Añadir filtro
        logging.info("Añadiendo filtro para buscar estudiante")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_addfilter"))
        ).click()

        # Paso 10: Verificar si el estudiante está en la lista
        logging.info("Verificando si el estudiante está en la lista")
        correo_encontrado = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.centeralign.cell.c1"))
        ).text

        nombre = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.centeralign.cell.c0 a"))
        ).text

        if correo == correo_encontrado:
            logging.info(f"Estudiante encontrado: {nombre}, {correo_encontrado}")
            
            # Almacenar el correo en sessionStorage
            logging.info("Almacenando correo del estudiante en sessionStorage")
            driver.execute_script(f"sessionStorage.setItem('correo_estudiante', '{correo}');")

            # Paso 11: Obtener monitores desde ActiveCampaign y almacenarlos
            logging.info("Consultando monitores desde ActiveCampaign")
            monitores = obtener_monitores()
            driver.execute_script(f"sessionStorage.setItem('monitores', JSON.stringify({monitores}));")
            logging.info(f"Monitores almacenados temporalmente en sessionStorage: {monitores}")

            return {"nombre": nombre, "correo": correo_encontrado, "existe": True, "monitores": monitores}
        else:
            logging.info("El correo encontrado no coincide.")
            return {"error": "Estudiante no encontrado", "existe": False}

    except Exception as e:
        logging.error(f"Error en el proceso de login y búsqueda: {e}")
        return {"error": str(e), "existe": False}