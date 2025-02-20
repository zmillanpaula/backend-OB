import os
import json
import logging
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from activeCampaignService import get_contact

# Configuración para Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.getenv("GOOGLE_SHEET_ID_REPO")  # ID de la hoja de Google desde variables de entorno
SHEET_NAME = 'Inventario-Asignación'

def extraer_licencia_cambridge_sheets(correo, nivel):
    try:
        # Cargar credenciales desde la variable de entorno en lugar de un archivo JSON
        SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON")
        creds_dict = json.loads(SERVICE_ACCOUNT_JSON)  # Convertir JSON en objeto Python
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)

        # Conectar con Google Sheets
        logging.info("Autenticando con Google Sheets API.")
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()

        # Leer datos de la hoja
        range_name = f'{SHEET_NAME}!A:G'
        logging.info(f"Accediendo al rango {range_name} del Google Sheet.")
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
        values = result.get('values', [])
        logging.info(f"Total de filas leídas: {len(values)}")

        if not values:
            logging.error("No se encontraron datos en la hoja.")
            return {"error": "La hoja está vacía."}

        # Buscar fila que coincida con el nivel y tenga la columna E vacía
        logging.info(f"Buscando filas disponibles para el nivel '{nivel}'.")
        for idx, row in enumerate(values, start=1):  # `start=1` para reflejar índice en Sheets
            while len(row) < 7:  # Asegurar que tenga al menos 7 columnas
                row.append("")

            if len(row) < 5:
                logging.warning(f"Fila {idx} no tiene suficientes columnas: {row}")
                continue

            if row[0].strip().upper() == nivel.strip().upper() and not row[4]:  # Nivel coincide y columna E está vacía
                codigo_licencia = row[2] if len(row) > 2 else None  # Columna C
                if not codigo_licencia:
                    logging.error(f"No se encontró código de licencia en la columna C de la fila {idx}.")
                    return {"error": "No hay código de licencia disponible para este nivel."}

                # Obtener fecha actual
                fecha_actual = datetime.now().strftime('%d/%m/%Y')

                # Consultar ActiveCampaign para obtener RUT/RUN y N° contrato
                logging.info(f"Consultando ActiveCampaign para el correo {correo}.")
                contacto = get_contact(correo)
                if not contacto:
                    logging.error(f"No se encontró contacto para el correo {correo}.")
                    return {"error": f"No se encontró contacto para el correo {correo}."}

                # Extraer RUT/RUN y número de contrato
                rut = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "36"), None)
                numero_contrato = next((fv["value"] for fv in contacto.get("fieldValues", []) if fv["field"] == "205"), None)

                if not rut or not numero_contrato:
                    logging.error("Datos insuficientes en ActiveCampaign para completar la hoja.")
                    return {"error": "No se pudo obtener RUT/RUN o N° contrato del contacto."}

                # Preparar actualizaciones en Google Sheets
                updates = [
                    {"range": f"{SHEET_NAME}!E{idx}", "values": [["VIRTUAL"]]},  # Estado "VIRTUAL"
                    {"range": f"{SHEET_NAME}!F{idx}", "values": [[numero_contrato]]},  # N° contrato
                    {"range": f"{SHEET_NAME}!G{idx}", "values": [[rut]]},  # RUT/RUN
                    {"range": f"{SHEET_NAME}!D{idx}", "values": [[fecha_actual]]},  # Fecha actual
                ]
                body = {"valueInputOption": "RAW", "data": updates}

                # Ejecutar las actualizaciones
                logging.info(f"Actualizando datos en Google Sheets para la fila {idx}.")
                sheet.values().batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()

                logging.info(f"Actualización completada para el nivel '{nivel}' en la fila {idx}.")
                return {
                    "codigo_licencia": codigo_licencia,
                    "nivel": nivel,
                    "fecha": fecha_actual,
                    "estado": "VIRTUAL",
                    "numero_contrato": numero_contrato,
                    "rut": rut,
                }

        # Si no se encuentra una fila válida
        logging.warning(f"No se encontraron filas disponibles para el nivel '{nivel}'.")
        return {"error": f"No se encontraron filas disponibles para el nivel '{nivel}'."}

    except HttpError as err:
        logging.error(f"Error al interactuar con Google Sheets: {err}")
        return {"error": f"Error al interactuar con Google Sheets: {err}"}
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        return {"error": f"Error inesperado: {e}"}