import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

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

def test_guardar_observacion(nivel_asignado, niveles_contratados, numero_contrato):
    driver = None  
    try:
        options = webdriver.ChromeOptions()
        driver = webdriver.Remote(command_executor=selenium_grid_url, options=options)

        driver.get("https://ventab.serpo.cl/inicio/bestwork")
        time.sleep(2)

        driver.find_element(By.ID, "exampleInputEmail1").send_keys("practicanted1")
        driver.find_element(By.ID, "exampleInputPassword1").send_keys("@OTSA2022")
        driver.find_element(By.CSS_SELECTOR, "input.btn-primary.auth-form-btn").click()
        time.sleep(3)

        driver.find_element(By.XPATH, "//a[@href='#ventas']").click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//a[@href='/admin/contratos/listar']").click()
        time.sleep(3)

        driver.find_element(By.XPATH, "//input[@class='search_init' and @index='4']").send_keys(numero_contrato)
        time.sleep(2)

        driver.find_element(By.CLASS_NAME, "btnobs").click()
        time.sleep(2)

        iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "modiframe"))
        )
        driver.switch_to.frame(iframe)

        mensaje = construir_mensaje(nivel_asignado, niveles_contratados)

        textarea = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[@name='obs']"))
        )
        textarea.clear()
        textarea.send_keys(mensaje)

        guardar_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "LoginButton"))
        )
        guardar_button.click()

        driver.switch_to.default_content()
        return {"success": True, "message": "Observación guardada correctamente."}

    except Exception as e:
        return {"error": str(e)}

    finally:
        if driver:
            driver.quit()