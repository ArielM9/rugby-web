import requests
import logging

# Configuración del logging para registrar los resultados de las pruebas
logging.basicConfig(filename='pruebas_api.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# URL de la API
API_URL = "http://127.0.0.1:8000"  # Aquí debes poner la URL de tu API, si es local o remota

# Funciones de prueba

def prueba_login():
    url = f"{API_URL}/login"
    datos = {
        "email": "usuario@dominio.com",
        "password": "contraseña123"
    }
    response = requests.post(url, json=datos)
    if response.status_code == 200:
        logging.info("Prueba POST /login - Éxito: %s", response.json())
    else:
        logging.error("Prueba POST /login - Error: %d - %s", response.status_code, response.text)

def prueba_registro():
    url = f"{API_URL}/registro"
    datos = {
        "nombre": "Juan Pérez",
        "email": "juan@dominio.com",
        "password": "contraseña123"
    }
    response = requests.post(url, json=datos)
    if response.status_code == 200:
        logging.info("Prueba POST /registro - Éxito: %s", response.json())
    else:
        logging.error("Prueba POST /registro - Error: %d - %s", response.status_code, response.text)

def prueba_favoritos():
    url = f"{API_URL}/favoritos"
    datos = {
        "usuario_id": 1,
        "favorito_id": 10
    }
    response = requests.post(url, json=datos)
    if response.status_code == 200:
        logging.info("Prueba POST /favoritos - Éxito: %s", response.json())
    else:
        logging.error("Prueba POST /favoritos - Error: %d - %s", response.status_code, response.text)

def prueba_get_favoritos():
    url = f"{API_URL}/favoritos/1"
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Prueba GET /favoritos/1 - Éxito: %s", response.json())
    else:
        logging.error("Prueba GET /favoritos/1 - Error: %d - %s", response.status_code, response.text)

def prueba_get_equipo():
    url = f"{API_URL}/equipo/1"
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Prueba GET /equipo/1 - Éxito: %s", response.json())
    else:
        logging.error("Prueba GET /equipo/1 - Error: %d - %s", response.status_code, response.text)

def prueba_get_partidos():
    url = f"{API_URL}/partidos"
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Prueba GET /partidos - Éxito: %s", response.json())
    else:
        logging.error("Prueba GET /partidos - Error: %d - %s", response.status_code, response.text)

def prueba_get_liga():
    url = f"{API_URL}/liga/1"
    response = requests.get(url)
    if response.status_code == 200:
        logging.info("Prueba GET /liga/1 - Éxito: %s", response.json())
    else:
        logging.error("Prueba GET /liga/1 - Error: %d - %s", response.status_code, response.text)

def prueba_delete_favoritos():
    url = f"{API_URL}/favoritos/1"
    response = requests.delete(url)
    if response.status_code == 200:
        logging.info("Prueba DELETE /favoritos/1 - Éxito: %s", response.json())
    else:
        logging.error("Prueba DELETE /favoritos/1 - Error: %d - %s", response.status_code, response.text)

# Ejecutar todas las pruebas
logging.info("Iniciando pruebas...")

prueba_login()
prueba_registro()
prueba_favoritos()
prueba_get_favoritos()
prueba_get_equipo()
prueba_get_partidos()
prueba_get_liga()
prueba_delete_favoritos()

logging.info("Pruebas finalizadas.")
