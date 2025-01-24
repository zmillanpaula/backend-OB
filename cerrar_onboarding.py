from selenium.webdriver.common.by import By
import logging
from datetime import datetime, timedelta
from activeCampaignService import get_contact
from selenium_manager import SeleniumManager
import os
import time


def cerrar_onboarding_form(data):
    """
    Completa y envía el formulario de cierre de onboarding en ActiveCampaign,
    asegurando el correcto manejo de datos y fechas.
    """
    url = "https://sedsa.activehosted.com/f/295"

    # Registrar los datos entrantes para depuración
    logging.info(f"Datos recibidos en cerrar_onboarding_form: {data}")
    print("Datos recibidos:", data)

    try:
        # Validación inicial
        required_fields = ["correo", "nivel", "monitor", "fecha_activacion"]
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"El campo requerido {field} está ausente o vacío.")

        # Obtener datos de ActiveCampaign
        contacto = get_contact(data["correo"])
        logging.info(f"Datos obtenidos de ActiveCampaign: {contacto}")
        if not contacto:
            logging.error(f"Contacto con correo {data['correo']} no encontrado.")
            return {"error": f"Contacto con correo {data['correo']} no encontrado en ActiveCampaign"}

        # Procesar campos de ActiveCampaign
        rut_original = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "36"), None)
        niveles_contratados = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "184"), None)

        # Validar valores extraídos
        if not rut_original or not niveles_contratados:
            raise ValueError("Faltan campos necesarios (RUT o niveles contratados) en los datos del contacto.")

        # Convertir niveles contratados a entero
        try:
            niveles_contratados = int(niveles_contratados)
        except ValueError:
            raise ValueError(f"El campo 'niveles contratados' tiene un valor no numérico: {niveles_contratados}")

        if not (1 <= niveles_contratados <= 10):  # Validar rango lógico
            raise ValueError(f"El valor de 'niveles contratados' ({niveles_contratados}) no es válido.")

        rut = rut_original.replace("-", "").strip()
        nombre = contacto.get("firstName", "").strip()
        apellido = contacto.get("lastName", "").strip()

        if not rut or not nombre or not apellido:
            raise ValueError("Faltan campos necesarios en ActiveCampaign para generar usuario y clave Moodle.")

        # Calcular usuario_moodle y clave_moodle
        usuario_moodle = rut
        clave_moodle = f"{apellido[0].upper()}{nombre[0].lower()}{rut_original}"

        # Calcular fecha de caducidad
        fecha_activacion = datetime.strptime(data["fecha_activacion"], "%d-%m-%Y")

        # Determinar meses a sumar según el nivel
        if data["nivel"] in ["1A", "1B", "2A", "2B"]:
            meses_a_sumar = 3
        elif data["nivel"] in ["3A", "3B", "4A", "4B", "5A", "5B", "6A", "6B"]:
            meses_a_sumar = 9
        else:
            raise ValueError(f"Nivel desconocido: {data['nivel']}")

        fecha_caducidad = fecha_activacion + timedelta(days=meses_a_sumar * 30)  # Aproximación de 30 días por mes
        # Convertir al formato DD-MM-YYYY con ceros iniciales si es necesario
        def add_leading_zero(value):
            return f"{int(value):02}"  # Convierte a entero y luego asegura dos dígitos

        fecha_activacion_str = f"{add_leading_zero(fecha_activacion.day)}-{add_leading_zero(fecha_activacion.month)}-{fecha_activacion.year}"
        fecha_caducidad_str = f"{add_leading_zero(fecha_caducidad.day)}-{add_leading_zero(fecha_caducidad.month)}-{fecha_caducidad.year}"

        nivel_message = "CAMPUS VIRTUAL" if data["nivel"] in ["1A", "1B", "2A", "2B"] else "CAMBRIDGE VIRTUAL"

        filled_fields = []  # Almacena los datos ingresados en el formulario

        with SeleniumManager() as driver:
            # Abrir el formulario
            driver.get(url)

            # Completar el formulario
            fields = [
                ("email", data["correo"]),
                ("field[371]", nivel_message),
                ("field[536]", "1.COMPLETADO CON EXITO"),
                ("field[370]", str(niveles_contratados * 3)),
                ("field[263]", data["nivel"]),
                ("field[264]", data["monitor"]),
                ("field[368]", usuario_moodle),
                ("field[369]", clave_moodle),
                ("field[365]", "NO APLICA"),
                ("field[328]", fecha_activacion_str),
                ("field[319]", fecha_caducidad_str),
                ("field[334]", fecha_caducidad_str),
                ("field[324]", data["nivel"]),
                ("field[343]", "Si"),
            ]

            for field_id, value in fields:
                try:
                    element = driver.find_element(By.ID, field_id)
                    if "field[" in field_id and "date" in element.get_attribute("type"):  # Para campos de fecha
                        element.click()  # Simular el clic para activar el calendario
                        time.sleep(0.5)  # Esperar para evitar problemas de sincronización
                        element.clear()  # Asegurarse de que el campo está vacío
                        # Ingresar la fecha dividida para evitar errores
                        day, month, year = value.split("-")
                        element.send_keys(day)
                        time.sleep(0.3)  # Pausa entre partes
                        element.send_keys(month)
                        time.sleep(0.3)
                        element.send_keys(year)
                    else:
                        logging.info(f"Llenando {field_id} con valor: {value}")
                        print(f"Llenando {field_id}: {value}")
                        element.send_keys(value)  # Escribir el valor
                    filled_fields.append({"field_id": field_id, "value": value})
                except Exception as e:
                    logging.error(f"Error al llenar el campo {field_id}: {e}")
                    print(f"Error al llenar el campo {field_id}: {e}")

            # Completar campos condicionales para niveles específicos
            if data["nivel"] in ["1A", "1B", "2A", "2B"]:
                cond_fields = [
                    ("field[508]", fecha_activacion_str),
                    ("field[509]", fecha_caducidad_str),
                    ("field[510]", data["nivel"]),
                ]
                for field_id, value in cond_fields:
                    try:
                        element = driver.find_element(By.ID, field_id)
                        element.click()
                        time.sleep(0.5)
                        element.clear()
                        day, month, year = value.split("-")
                        element.send_keys(day)
                        time.sleep(0.3)
                        element.send_keys(month)
                        time.sleep(0.3)
                        element.send_keys(year)
                        logging.info(f"Llenando {field_id} con valor: {value}")
                        print(f"Llenando {field_id}: {value}")
                        filled_fields.append({"field_id": field_id, "value": value})
                    except Exception as e:
                        logging.error(f"Error al llenar el campo {field_id}: {e}")
                        print(f"Error al llenar el campo {field_id}: {e}")

            # Guardar un pantallazo del formulario lleno
            screenshot_dir = "screenshots"
            if not os.path.exists(screenshot_dir):
                os.makedirs(screenshot_dir)
            screenshot_path = os.path.join(screenshot_dir, "onboarding_form_filled.png")
            driver.save_screenshot(screenshot_path)
            logging.info(f"Pantallazo guardado antes de enviar: {screenshot_path}")
            print(f"Pantallazo guardado antes de enviar: {screenshot_path}")

            # Enviar el formulario
            driver.find_element(By.XPATH, "//button[contains(text(), 'Enviar')]").click()
            logging.info("Formulario enviado con éxito.")
            print("Formulario enviado con éxito.")

            # Retornar los datos calculados y los ingresados
            return {
                "message": "Formulario enviado con éxito.",
                "correo": data["correo"],
                "nivel": data["nivel"],
                "monitor": data["monitor"],
                "usuario_moodle": usuario_moodle,
                "clave_moodle": clave_moodle,
                "fecha_activacion": fecha_activacion_str,
                "fecha_caducidad": fecha_caducidad_str,
                "datos_ingresados": filled_fields,  # Devuelve los datos ingresados
            }

    except Exception as e:
        logging.error(f"Error al completar el formulario: {e}")
        print(f"Error al completar el formulario: {e}")
        return {"error": str(e)}