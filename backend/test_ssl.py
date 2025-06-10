import requests
import certifi

print("Caminho do cacert.pem:", certifi.where())
try:
    r = requests.get("https://www.google.com", verify=certifi.where())
    print("Status code:", r.status_code)
    print("Conexão HTTPS OK!")
except Exception as e:
    print("Erro ao conectar:", e)