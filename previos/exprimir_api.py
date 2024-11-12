import pymysql
import requests

# Configuración de la base de datos
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,  # Devuelve los resultados como diccionarios
    'ssl': {'ssl': {'ca': None}}  # Para ignorar los problemas de SSL
}

API_URL = "https://v1.rugby.api-sports.io"
API_KEY = "53bb4992e1615b3310bd9dc23b0335c4"

# Lista de países con IDs
countries = [
    {'id': 1, 'name': "Argentina"},
    {'id': 2, 'name': "Australia"},
    {'id': 3, 'name': "Austria"},
    {'id': 4, 'name': "Canada"},
    {'id': 5, 'name': "Czech-Republic"},
    {'id': 6, 'name': "England"},
    {'id': 7, 'name': "France"},
    {'id': 8, 'name': "Georgia"},
    {'id': 9, 'name': "Germany"},
    {'id': 10, 'name': "Ireland"},
    {'id': 11, 'name': "Italy"},
    {'id': 12, 'name': "Japan"},
    {'id': 13, 'name': "Netherlands"},
    {'id': 14, 'name': "New-Zealand"},
    {'id': 15, 'name': "Poland"},
    {'id': 16, 'name': "Portugal"},
    {'id': 17, 'name': "Romania"},
    {'id': 18, 'name': "Russia"},
    {'id': 19, 'name': "Scotland"},
    {'id': 20, 'name': "South-Africa"},
    {'id': 21, 'name': "Spain"},
    {'id': 22, 'name': "USA"},
    {'id': 23, 'name': "Wales"},
    {'id': 24, 'name': "Kenya"}
]

def get_teams_by_country(country_id):
    url = f"{API_URL}/teams?country_id={country_id}"
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(f"Error al obtener equipos para el país {country_id}: {response.status_code} - {response.text}")

def get_all_leagues():
    url = f"{API_URL}/leagues"
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["response"]
    else:
        raise Exception(f"Error al obtener ligas: {response.status_code} - {response.text}")

def insert_team(connection, team, country_name):
    with connection.cursor() as cursor:
        print(f"Inserting team: '{team['name']}' with length {len(team['name'])}")  # Imprimir nombre y longitud
        # Verificar si el equipo ya existe antes de insertarlo
        sql_check = "SELECT COUNT(*) FROM equipos WHERE id = %s"
        cursor.execute(sql_check, (team['id'],))
        exists = cursor.fetchone()['COUNT(*)']
        
        if exists == 0:
            sql = "INSERT INTO equipos (id, nombre, logo, pais) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (team['id'], team['name'], team['logo'], country_name))

def insert_league(connection, league):
    with connection.cursor() as cursor:
        print(f"Inserting league: '{league['name']}' with length {len(league['name'])}")  # Imprimir nombre y longitud
        # Verificar si la liga ya existe antes de insertarla
        sql_check = "SELECT COUNT(*) FROM ligas WHERE id = %s"
        cursor.execute(sql_check, (league['id'],))
        exists = cursor.fetchone()['COUNT(*)']
        
        if exists == 0:
            sql = "INSERT INTO ligas (id, nombre, logo, pais) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (league['id'], league['name'], league['logo'], league['country']['name']))

def fill_database():
    connection = pymysql.connect(**db_config)
    
    try:
        for country in countries:
            country_id = country['id']
            country_name = country['name']
            
            # Obtener y guardar equipos
            teams = get_teams_by_country(country_id)
            for team in teams:
                insert_team(connection, team, country_name)
            
            # Obtener y guardar ligas
            leagues = get_all_leagues()
            for league in leagues:
                insert_league(connection, league)

        connection.commit()

    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()

    finally:
        connection.close()

if __name__ == "__main__":
    fill_database()