import os
import json
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials
import logging

# Mapeo de niveles a columnas (P-AL)
NIVELES_COLUMNAS = {
    "1A": "P", "1B": "R",
    "2A": "T", "2B": "V",
    "3A": "X", "3B": "Z",
    "4A": "AB", "4B": "AD",
    "5A": "AF", "5B": "AH",
    "6A": "AJ", "6B": "AL",
}

# Configurar logging para depuración
logging.basicConfig(level=logging.INFO)

def autenticar_google_sheets():
    """Autenticación con Google Sheets usando credenciales almacenadas en variable de entorno."""
    try:
        creds_json = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS", "{}"))  # Evitar errores si la variable no está definida
        creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        return gspread.authorize(creds)
    except Exception as e:
        logging.error(f"❌ Error al autenticar Google Sheets: {e}")
        return None

def buscar_fila_por_correo(sheet, correo):
    """Busca la fila donde se encuentra el correo en la columna G."""
    valores_columna_g = sheet.col_values(7)  # Columna G (correos)
    for i, valor in enumerate(valores_columna_g):
        if valor.strip().lower() == correo.strip().lower():
            return i + 1  # Google Sheets usa indexación desde 1
    return None  # No encontrado

def extraer_niveles_contratados(texto):
    """Extrae la cantidad de niveles contratados desde la columna D."""
    match = re.search(r"(\d+)", texto)
    return int(match.group(1)) if match else 1  # Si no encuentra, por defecto 1 nivel

def determinar_tipo_curso(nivel):
    """Determina el valor de la columna M según el nivel."""
    return "Campus" if nivel in {"1A", "1B", "2A", "2B"} else "x"

def obtener_siguiente_columna(columna):
    """Obtiene la siguiente columna en la progresión de niveles."""
    columnas = list(NIVELES_COLUMNAS.values())
    if columna in columnas:
        index = columnas.index(columna)
        return columnas[index + 1] if index + 1 < len(columnas) else None
    return None

def marcar_proyeccion(sheet, fila, nivel_inicio, niveles_contratados):
    """Marca la proyección de niveles en las columnas P-AL."""
    if nivel_inicio not in NIVELES_COLUMNAS:
        logging.warning(f"⚠️ Nivel {nivel_inicio} no encontrado en la configuración.")
        return

    columna_actual = NIVELES_COLUMNAS[nivel_inicio]
    sheet.update_acell(f"{columna_actual}{fila}", "C")
    logging.info(f"✅ Marcado 'C' en {columna_actual}{fila}")

    for _ in range(niveles_contratados - 1):
        columna_actual = obtener_siguiente_columna(columna_actual)
        if columna_actual:
            sheet.update_acell(f"{columna_actual}{fila}", "x")
            logging.info(f"✅ Marcado 'x' en {columna_actual}{fila}")
        else:
            logging.warning("⚠️ Se alcanzó el límite de niveles en la hoja.")
            break

def actualizar_fila_en_google_sheets(correo, nivel):
    """Actualiza la fila en Google Sheets con los datos del estudiante."""
    try:
        client = autenticar_google_sheets()
        if not client:
            return {"error": "No se pudo autenticar con Google Sheets."}

        sheet = client.open_by_key("1lbdMTevzeZm4RTR3FPT77qtK6KcI2Q3U5squ2UNHJug").worksheet("DOCENCIA (todas las sedes)")

        fila = buscar_fila_por_correo(sheet, correo)
        if not fila:
            logging.warning(f"⚠️ Correo {correo} no encontrado en la planilla.")
            return {"error": f"Correo {correo} no encontrado."}

        texto_niveles = sheet.cell(fila, 4).value  # Columna D (meses contratados)
        niveles_contratados = extraer_niveles_contratados(texto_niveles)
        fraccion_niveles = f"1/{niveles_contratados}"  # Formato de nivel

        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        tipo_curso = determinar_tipo_curso(nivel)

        # Escribir datos en columnas H-M
        valores = ["OK", nivel, fraccion_niveles, fecha_actual, correo, tipo_curso]
        for col, valor in enumerate(valores, start=8):
            sheet.update_cell(fila, col, valor)
            logging.info(f"✅ Escrito '{valor}' en fila {fila}, columna {col}")

        # Marcar proyección en la hoja (columnas P-AL)
        marcar_proyeccion(sheet, fila, nivel, niveles_contratados)

        logging.info(f"🎉 Actualización completa para {correo} ({nivel}, {niveles_contratados} niveles)")
        return {"success": True, "message": "Planilla actualizada correctamente."}

    except Exception as e:
        logging.error(f"❌ Error en actualizar_fila_en_google_sheets: {e}")
        return {"error": str(e)}