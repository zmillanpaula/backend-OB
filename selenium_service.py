from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def run_selenium_task():
    chrome_service = Service("/usr/local/bin/chromedriver")  # Cambia esta ruta si es necesario
    options = Options()
    options.headless = False  # Quita el modo headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--display=:1")  # Display que usa el servidor VNC

    driver = webdriver.Chrome(service=chrome_service, options=options)
    driver.get("https://example.com")

    print("Título de la página:", driver.title)

    driver.save_screenshot("screenshot.png")
    driver.quit()