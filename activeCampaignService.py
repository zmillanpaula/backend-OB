# services/activeCampaignService.py
import requests
import logging

API_URL = "https://sedsa.api-us1.com"
API_KEY = "d2830a151e2d5ae79ee56b3bf8035c9728d27a1c75fbd2fe89eff5f11c57f078c0f93ae1"

def get_contact(email):
    """
    Recupera los datos de un contacto desde ActiveCampaign, incluidos los valores de campos personalizados.
    También extrae directamente campos clave como RUT y niveles contratados.
    """
    headers = {"Api-Token": API_KEY}
    email = email.strip().lower()
    print(f"Buscando correo: {email}")

    try:
        # Obtener datos básicos del contacto
        response = requests.get(f"{API_URL}/api/3/contacts", headers=headers, params={"email": email})
        print(f"Estado de respuesta: {response.status_code}")
        print(f"Datos de respuesta: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if not data.get("contacts"):
                print(f"No se encontró un contacto con el correo: {email}")
                return None

            contacto = data["contacts"][0]

            # Recuperar valores personalizados (fieldValues)
            field_values_link = contacto["links"].get("fieldValues")
            if field_values_link:
                field_values_response = requests.get(field_values_link, headers=headers)
                print(f"Estado de respuesta para fieldValues: {field_values_response.status_code}")
                print(f"Datos de fieldValues: {field_values_response.json()}")

                if field_values_response.status_code == 200:
                    contacto["fieldValues"] = field_values_response.json().get("fieldValues", [])
                else:
                    print(f"Error al recuperar fieldValues para el contacto: {field_values_response.text}")
                    contacto["fieldValues"] = []
            else:
                print(f"No se encontró un enlace para fieldValues en el contacto.")
                contacto["fieldValues"] = []

            # Procesar campos clave directamente desde fieldValues
            contacto["rut"] = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "36"), None)
            contacto["niveles_contratados"] = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "370"), "1")

            return contacto

        else:
            print(f"Error al buscar el contacto: {response.text}")
            return None

    except requests.RequestException as e:
        print(f"Error en la solicitud a ActiveCampaign: {e}")
        return None
    
def extraer_rut(field_values):
    """
    Busca el campo personalizado RUT/RUN (field ID 36) en los valores de campo personalizados.
    """
    for field in field_values:
        if field.get("field") == "36":  # ID del campo RUT/RUN
            return field.get("value", "").replace("-", "").strip()
    return None    

def obtener_opciones_campo(field_id):
    """
    Recupera las opciones de un campo personalizado en ActiveCampaign.
    """
    headers = {"Api-Token": API_KEY}
    try:
        logging.info(f"Consultando opciones del campo con ID {field_id}")
        response = requests.get(f"{API_URL}/fields/{field_id}/options", headers=headers)

        if response.status_code == 200:
            opciones = response.json().get("fieldOptions", [])
            return [opcion["value"] for opcion in opciones]  # Extrae los valores
        else:
            logging.error(f"Error al obtener opciones del campo {field_id}: {response.text}")
            return None
    except requests.RequestException as e:
        logging.error(f"Error en la solicitud: {e}")
        return None


def submit_form(payload):
    headers = {"Content-Type": "application/json"}
    response = requests.post("https://sedsa.activehosted.com/proc.php", headers=headers, json=payload)
    return response.status_code == 200

def get_contact_with_details(email):
    """
    Obtiene los datos detallados del contacto en ActiveCampaign, incluyendo RUT, número de contrato,
    meses y niveles contratados, sin afectar la función original `get_contact()`.
    """
    headers = {"Api-Token": API_KEY}
    email = email.strip().lower()
    
    try:
        # 1️⃣ Consultar el contacto por email
        response = requests.get(f"{API_URL}/api/3/contacts", headers=headers, params={"email": email})
        
        if response.status_code != 200:
            logging.error(f"Error en la consulta a ActiveCampaign: {response.text}")
            return None

        data = response.json()
        if not data.get("contacts"):
            logging.warning(f"No se encontró contacto con el correo: {email}")
            return None

        contacto = data["contacts"][0]

        # 2️⃣ Obtener los valores personalizados (fieldValues)
        field_values_link = contacto["links"].get("fieldValues")
        field_values = []
        if field_values_link:
            field_values_response = requests.get(field_values_link, headers=headers)
            if field_values_response.status_code == 200:
                field_values = field_values_response.json().get("fieldValues", [])
            else:
                logging.warning(f"Error obteniendo fieldValues: {field_values_response.text}")

        # 3️⃣ Extraer datos clave de fieldValues
        def get_field_value(field_values, field_id):
            """Busca un campo específico dentro de los fieldValues y devuelve su valor."""
            return next((fv["value"] for fv in field_values if fv["field"] == field_id), None)

        return {
            "correo": email,
            "rut": get_field_value(field_values, "36"),  # RUT
            "nombre": contacto.get("firstName", "").strip(),
            "apellido": contacto.get("lastName", "").strip(),
            "numero_contrato": get_field_value(field_values, "205"),  # Número de contrato
            "meses_contratados": int(get_field_value(field_values, "370") or 1),  # Meses contratados
            "niveles_contratados": int(get_field_value(field_values, "184") or 1),  # Niveles contratados
        }

    except requests.RequestException as e:
        logging.error(f"Error en la solicitud a ActiveCampaign: {e}")
        return None