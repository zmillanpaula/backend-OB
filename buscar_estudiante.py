import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from activeCampaignService import get_contact

def obtener_monitores():
    """
    Obtiene la lista de monitores (campo personalizado con ID 149) desde ActiveCampaign.
    """
    logging.info("📡 Consultando monitores desde ActiveCampaign...")
    
    campo_monitor_id = "149"
    monitores = []
    
    try:
        contacto = get_contact("dummy@example.com")  # 🔹 Consulta un contacto para obtener la lista
        
        if not contacto or not contacto.get("fieldValues"):
            logging.warning("⚠️ No se encontraron valores personalizados para los monitores.")
            return []

        monitores = set()
        for field in contacto.get("fieldValues", []):
            if field.get("field") == campo_monitor_id:
                monitores.add(field.get("value", "").strip())

        logging.info(f"✅ Monitores obtenidos: {monitores}")
        return list(monitores)

    except Exception as e:
        logging.error(f"❌ Error al obtener monitores: {e}")
        return [] 

def buscar_estudiante(driver, correo):
    """
    Busca al estudiante en Campus Virtual y guarda su información.
    """
    try:
        logging.info(f"🔍 Buscando estudiante con correo: {correo}")

        # 🔹 Verificar si la sesión sigue activa
        try:
            driver.current_window_handle  # Intenta acceder a la sesión actual
        except:
            logging.warning("⚠️ Sesión de Selenium perdida. Reiniciando WebDriver...")
            return {"error": "Sesión de Selenium perdida. Intenta nuevamente.", "existe": False}

        # 🔹 Navegar a la búsqueda de usuarios
        driver.get("https://campusvirtual.bestwork.cl/admin/user.php")
        
        # 🔹 Mostrar más opciones de búsqueda
        logging.info("📌 Expandiendo opciones de búsqueda...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Mostrar más..."))
        ).click()

        # 🔹 Ingresar correo del estudiante
        logging.info("✉️ Ingresando correo del estudiante...")
        email_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "id_email"))
        )
        email_input.clear()
        email_input.send_keys(correo)

        # 🔹 Añadir filtro y buscar
        logging.info("🔎 Aplicando filtro de búsqueda...")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "id_addfilter"))
        ).click()

        # 🔹 Verificar si el estudiante fue encontrado
        logging.info("✅ Verificando resultados...")
        correo_encontrado = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.centeralign.cell.c1"))
        ).text

        nombre = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "td.centeralign.cell.c0 a"))
        ).text

        if correo == correo_encontrado:
            logging.info(f"👤 Estudiante encontrado: {nombre}, {correo_encontrado}")

            # 🔹 Almacenar correo en sessionStorage
            logging.info("📌 Guardando correo en sessionStorage...")
            driver.execute_script(f"sessionStorage.setItem('correo_estudiante', '{correo}');")

            # 🔹 Obtener y almacenar monitores
            monitores = obtener_monitores()
            driver.execute_script(f"sessionStorage.setItem('monitores', JSON.stringify({monitores}));")
            logging.info(f"✅ Monitores almacenados temporalmente: {monitores}")

            return {"nombre": nombre, "correo": correo_encontrado, "existe": True, "monitores": monitores}
        
        else:
            logging.info("⚠️ No se encontró el estudiante.")
            return {"error": "Estudiante no encontrado", "existe": False}

    except Exception as e:
        logging.error(f"❌ Error en la búsqueda del estudiante: {e}")
        return {"error": str(e), "existe": False}