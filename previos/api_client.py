import requests

API_URL = "https://api-sports.io/rugby/v1"
API_KEY = "53bb4992e1615b3310bd9dc23b0335c4"  # Mueve la API key aquí

# Función para obtener equipos
def get_teams():
    url = f"{API_URL}/teams"
    headers = {
        "x-apisports-key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["response"]  # Ajusta esto según la estructura de la API
    else:
        raise Exception(f"Error al obtener equipos: {response.status_code} - {response.text}")

# Función para obtener ligas
def get_leagues():
    url = f"{API_URL}/leagues"
    headers = {
        "x-apisports-key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["response"]  # Ajusta esto según la estructura de la API
    else:
        raise Exception(f"Error al obtener ligas: {response.status_code} - {response.text}")

# Función para obtener países
def get_countries():
    url = f"{API_URL}/countries"
    headers = {
        "x-apisports-key": API_KEY
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["response"]  # Ajusta esto según la estructura de la API
    else:
        raise Exception(f"Error al obtener países: {response.status_code} - {response.text}")

# Aquí puedes agregar más funciones según lo que necesites de la API
