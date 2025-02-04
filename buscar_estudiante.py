import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def buscar_estudiante(driver, correo):
    """
    Busca al estudiante en Campus Virtual y guarda su información.
    """
    try:
        logging.info(f"🔍 Buscando estudiante con correo: {correo}")

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
            return {"nombre": nombre, "correo": correo_encontrado, "existe": True}
        
        else:
            logging.info("⚠️ No se encontró el estudiante.")
            return {"error": "Estudiante no encontrado", "existe": False}

    except Exception as e:
        logging.error(f"❌ Error en la búsqueda del estudiante: {e}")
        return {"error": str(e), "existe": False}
    
    finally:
        logging.info("Cerrando webdriver")
        driver.quit()