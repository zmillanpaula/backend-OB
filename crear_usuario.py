import sys
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def main():
    try:
        # Recibir parámetros desde la línea de comandos
        nombre, apellido, correo, telefono, rut = sys.argv[1:]
        print(f"Creando usuario: {nombre} {apellido}, Correo: {correo}, Teléfono: {telefono}, RUT: {rut}")

        # Configuración de ChromeDriver
        driver = webdriver.Chrome()  # Asegúrate de que ChromeDriver está configurado correctamente
        print("Navegador iniciado correctamente.")

        # Abre la página de inicio de sesión
        driver.get("https://campusvirtual.bestwork.cl/login/index.php")
        print("Página de inicio de sesión cargada.")

        # Localizar y completar los campos de inicio de sesión
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        ).send_keys("TU_USUARIO")  # Reemplaza con el usuario real

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "password"))
        ).send_keys("TU_CONTRASEÑA")  # Reemplaza con la contraseña real

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "loginbtn"))
        ).click()
        print("Inicio de sesión exitoso.")

        # Navegar a la página de creación de usuarios
        driver.get("https://campusvirtual.bestwork.cl/user/editadvanced.php?id=-1")
        print("Página de creación de usuarios cargada.")

        # Completar el formulario de creación de usuario
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='username']"))
        ).send_keys(rut)  # Usar el RUT como usuario

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='firstname']"))
        ).send_keys(nombre)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='lastname']"))
        ).send_keys(apellido)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='email']"))
        ).send_keys(correo)

        # Enviar el formulario (ajusta el selector si es necesario)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='submit']"))
        ).click()
        print("Formulario enviado con éxito.")

        # Cerrar el navegador
        driver.quit()
        print("Usuario creado exitosamente.")

    except Exception as e:
        print(f"Error en la automatización: {e}")

if __name__ == "__main__":
    main()
