from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# Conexión al servidor Selenium en el contenedor
options = webdriver.ChromeOptions()
driver = webdriver.Remote(
    command_executor='http://localhost:4444/wd/hub',  # Puerto 4444 de Selenium
    options=options
)

try:
    # Navegar a Google
    driver.get("https://www.google.com")
    print("Título de la página:", driver.title)

    # Interactuar con la barra de búsqueda
    search_box = driver.find_element(By.NAME, "q")
    search_box.send_keys("Selenium noVNC" + Keys.RETURN)

    # Esperar unos segundos
    driver.implicitly_wait(5)

    # Capturar captura de pantalla
    driver.save_screenshot("screenshot.png")
    print("Captura guardada como 'screenshot.png'")
finally:
    driver.quit()