import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 🌐 Configurar Selenium Grid
selenium_grid_url = "http://localhost:4444/wd/hub"

def construir_mensaje(nivel_asignado, niveles_contratados):
    evolve_niveles = {"3A", "3B", "4A", "4B", "5A", "5B", "6A", "6B"}
    campus_virtual_niveles = {"1A", "1B", "2A", "2B"}

    if nivel_asignado in evolve_niveles:
        plataforma = "Evolve"
    elif nivel_asignado in campus_virtual_niveles:
        plataforma = "Campus virtual"
    else:
        plataforma = "Desconocido"

    return f"Activa nivel {nivel_asignado} (1/{niveles_contratados}) - {plataforma}"

def test_guardar_observacion(nivel_asignado, niveles_contratados):
    driver = None  
    try:
        options = webdriver.ChromeOptions()
        driver = webdriver.Remote(command_executor=selenium_grid_url, options=options)

        driver.get("https://ventab.serpo.cl/inicio/bestwork")
        time.sleep(2)

        # 🔹 Hacer login
        driver.find_element(By.ID, "exampleInputEmail1").send_keys("practicanted1")
        driver.find_element(By.ID, "exampleInputPassword1").send_keys("@OTSA2022")
        driver.find_element(By.CSS_SELECTOR, "input.btn-primary.auth-form-btn").click()
        time.sleep(3)

        # 🔹 Navegar a contratos
        driver.find_element(By.XPATH, "//a[@href='#ventas']").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//a[@href='/admin/contratos/listar']").click()
        time.sleep(3)

        # 🔹 Buscar contrato
        driver.find_element(By.XPATH, "//input[@class='search_init' and @index='4']").send_keys("7083")
        time.sleep(2)

        # 🔹 Abrir observaciones
        driver.find_element(By.CLASS_NAME, "btnobs").click()
        time.sleep(2)

        # 🔹 Esperar a que el iframe aparezca y cambiar a él
        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "modiframe"))
        )
        driver.switch_to.frame(iframe)
        logging.info("✅ Cambiado al iframe correctamente.")

        # 🔹 Generar la frase con la lógica de nivel y niveles contratados
        mensaje = construir_mensaje(nivel_asignado, niveles_contratados)
        logging.info(f"📝 Mensaje generado: {mensaje}")

        # 🔹 Buscar y escribir en el textarea
        try:
            textarea = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//textarea[@name='obs']"))
            )
            textarea.clear()
            textarea.send_keys(mensaje)
            logging.info("✅ Mensaje ingresado en el textarea correctamente.")
        except Exception as e:
            logging.error(f"❌ No se pudo escribir en el textarea: {e}")
            return {"error": "No se pudo escribir en el textarea."}

        # 🔹 Presionar el botón "Guardar"
        try:
            guardar_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "LoginButton"))
            )
            guardar_button.click()
            logging.info("✅ Se hizo clic en 'Guardar'.")
        except:
            try:
                guardar_button = driver.find_element(By.ID, "LoginButton")
                driver.execute_script("arguments[0].scrollIntoView();", guardar_button)
                guardar_button.click()
                logging.info("✅ Se hizo clic en 'Guardar' después de hacer scroll.")
            except:
                try:
                    guardar_button = driver.find_element(By.ID, "LoginButton")
                    driver.execute_script("arguments[0].click();", guardar_button)
                    logging.info("✅ Se hizo clic en 'Guardar' con JavaScript.")
                except Exception as e:
                    logging.error(f"❌ No se pudo hacer clic en 'Guardar': {e}")
                    return {"error": "No se encontró o no se pudo presionar el botón 'Guardar'."}

        # 🔹 Salir del iframe y volver al contexto principal
        driver.switch_to.default_content()
        logging.info("✅ Regresamos al contexto principal.")

        input("🔎 Revisa la pantalla en SERPO. Presiona ENTER para cerrar el navegador...")
        return {"success": True, "message": "Observación guardada correctamente."}

    except Exception as e:
        logging.error(f"❌ Error en el proceso: {e}", exc_info=True)
        return {"error": str(e)}

    finally:
        if driver:
            logging.info("🛑 Cerrando el navegador.")
            driver.quit()

if __name__ == "__main__":
    nivel_asignado = input("Ingrese el nivel asignado (ej: 3A, 2B, 6A, etc.): ").strip().upper()
    niveles_contratados = input("Ingrese el número de niveles contratados: ").strip()
    
    resultado = test_guardar_observacion(nivel_asignado, niveles_contratados)
    print(resultado)