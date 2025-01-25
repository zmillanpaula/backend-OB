import requests

try:
    response = requests.get("http://localhost:4444/wd/hub/status", timeout=5)
    print("Conexión exitosa:", response.json())
except Exception as e:
    print("Error de conexión:", e)