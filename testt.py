import os
import json
import gspread
from google.oauth2.service_account import Credentials

def autenticar_google_sheets():
    """Prueba la autenticación con Google Sheets."""
    try:
        google_sheets_credentials = os.getenv("GOOGLE_SHEETS_CREDENTIALS")

        if not google_sheets_credentials:
            print("❌ No se encontró GOOGLE_SHEETS_CREDENTIALS en las variables de entorno.")
            return None

        # Verificar que el JSON esté bien formado
        try:
            creds_json = json.loads(google_sheets_credentials.replace("\\n", "\n"))  # Corregir saltos de línea
        except json.JSONDecodeError as e:
            print(f"❌ Error al parsear GOOGLE_SHEETS_CREDENTIALS: {e}")
            return None

        creds = Credentials.from_service_account_info(creds_json, scopes=["https://www.googleapis.com/auth/spreadsheets"])
        client = gspread.authorize(creds)

        print("✅ Autenticación con Google Sheets exitosa.")
        return client

    except Exception as e:
        print(f"❌ Error general en autenticación: {e}")
        return None

# 🚀 PRUEBA EL SCRIPT
if __name__ == "__main__":
    client = autenticar_google_sheets()
    if client:
        print("🎉 Prueba completada con éxito.")
    else:
        print("⚠️ Prueba fallida.")