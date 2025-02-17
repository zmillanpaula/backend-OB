import os
import json
import gspread
import re
from datetime import datetime
from google.oauth2.service_account import Credentials

# Mapeo de niveles a columnas (P-AL)
NIVELES_COLUMNAS = {
    "1A": "P", "1B": "R",
    "2A": "T", "2B": "V",
    "3A": "X", "3B": "Z",
    "4A": "AB", "4B": "AD",
    "5A": "AF", "5B": "AH",
    "6A": "AJ", "6B": "AL",
}

# Autenticación con Google Sheets
def autenticar_google_sheets():
    creds_json = json.loads(os.getenv("GOOGLE_SHEETS_CREDENTIALS"))
    creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    return gspread.authorize(creds)

# Buscar la fila donde se encuentra el correo en la columna G
def buscar_fila_por_correo(sheet, correo):
    valores_columna_g = sheet.col_values(7)  # Columna G (correos)
    for i, valor in enumerate(valores_columna_g):
        if valor.strip().lower() == correo.strip().lower():
            return i + 1  # Google Sheets usa indexación desde 1
    return None  # No encontrado

# Extraer la cantidad de niveles contratados desde la columna D
def extraer_niveles_contratados(texto):
    match = re.search(r"(\d+)", texto)  # Buscar solo el número dentro del texto
    return int(match.group(1)) if match else 1  # Si no encuentra, por defecto 1 nivel

# Extraer el número de niveles desde la columna D y calcular "1/X"
def extraer_fraccion_niveles(texto):
    match = re.search(r"(\d+)", texto)
    return f"1/{match.group(1)}" if match else "1/?"

# Determinar el valor de la columna M según el nivel
def determinar_tipo_curso(nivel):
    return "Campus" if nivel in {"1A", "1B", "2A", "2B"} else "x"

# Obtener la siguiente columna en la progresión de niveles
def obtener_siguiente_columna(columna):
    columnas = list(NIVELES_COLUMNAS.values())
    if columna in columnas:
        index = columnas.index(columna)
        return columnas[index + 1] if index + 1 < len(columnas) else None
    return None

# Marcar proyección de niveles en las columnas P-AL
def marcar_proyeccion(sheet, fila, nivel_inicio, niveles_contratados):
    if nivel_inicio not in NIVELES_COLUMNAS:
        print(f"⚠️ Nivel {nivel_inicio} no encontrado en la configuración.")
        return

    # Determinar la columna de inicio
    columna_actual = NIVELES_COLUMNAS[nivel_inicio]
    sheet.update_acell(f"{columna_actual}{fila}", "C")  # Marcar "C" en la columna de inicio
    print(f"✅ Marcado 'C' en {columna_actual}{fila}")

    # Marcar "x" en los siguientes niveles contratados
    for _ in range(niveles_contratados - 1):
        columna_actual = obtener_siguiente_columna(columna_actual)
        if columna_actual:
            sheet.update_acell(f"{columna_actual}{fila}", "x")
            print(f"✅ Marcado 'x' en {columna_actual}{fila}")
        else:
            print("⚠️ Se alcanzó el límite de niveles en la hoja.")
            break

# Función principal para actualizar Google Sheets
def actualizar_fila_en_google_sheets(correo, nivel):
    try:
        client = autenticar_google_sheets()
        sheet = client.open_by_key("19yQpnp42OdbOEn-pdp5EfI9Y_ujFmw7rd8JgeETh43A").worksheet("DOCENCIA (todas las sedes)")

        fila = buscar_fila_por_correo(sheet, correo)
        if not fila:
            print(f"⚠️ Correo {correo} no encontrado.")
            return

        # Obtener información de niveles desde la columna D
        texto_niveles = sheet.cell(fila, 4).value  # Columna D
        niveles_contratados = extraer_niveles_contratados(texto_niveles)
        fraccion_niveles = extraer_fraccion_niveles(texto_niveles)

        # Obtener fecha actual en formato dd/mm/YYYY
        fecha_actual = datetime.now().strftime("%d/%m/%Y")

        # Determinar el valor de la columna M
        tipo_curso = determinar_tipo_curso(nivel)

        # Escribir datos en columnas H-M
        valores = ["OK", nivel, fraccion_niveles, fecha_actual, correo, tipo_curso]
        for col, valor in enumerate(valores, start=8):
            sheet.update_cell(fila, col, valor)
            print(f"✅ Escrito '{valor}' en fila {fila}, columna {col}")

        # Marcar proyección en la hoja (columnas P-AL)
        marcar_proyeccion(sheet, fila, nivel, niveles_contratados)

        print(f"\n🎉 Actualización completa para {correo} ({nivel}, {niveles_contratados} niveles)")

    except Exception as e:
        print(f"\n❌ Error en la actualización: {e}")

# Ejemplo de uso
if __name__ == "__main__":
    email_usuario = input("Ingrese el correo del estudiante: ").strip().lower()
    nivel_usuario = input("Ingrese el nivel (ej. 1A, 3B, 5A): ").strip().upper()
    actualizar_fila_en_google_sheets(email_usuario, nivel_usuario)