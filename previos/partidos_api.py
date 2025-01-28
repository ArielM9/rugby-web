import pymysql
import requests
from datetime import datetime, timedelta

# Configuración de la base de datos
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,
    'ssl': {'ssl': {'ca': None}}
}

API_URL = "https://v1.rugby.api-sports.io"
API_KEY = "53bb4992e1615b3310bd9dc23b0335c4"

# Función para obtener los partidos de una fecha específica
def get_games_by_date(date):
    url = f"{API_URL}/games?date={date}"
    headers = {"x-apisports-key": API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print(f"Partidos obtenidos para la fecha {date}: {len(response.json()['response'])} partidos.")
        return response.json()["response"]
    else:
        raise Exception(f"Error al obtener partidos para la fecha {date}: {response.status_code} - {response.text}")

# Función para insertar partido en la base de datos
def insert_game(connection, game):
    with connection.cursor() as cursor:
        
        # Separar la fecha y hora, y formatear la hora para eliminar el offset
        date_part = game['date'].split("T")[0]  # Fecha en formato YYYY-MM-DD
        time_part = game['date'].split("T")[1].split("+")[0]  # Hora en formato HH:MM:SS, sin offset

        sql = """
        INSERT INTO partidos (id, id_local, id_visitante, fecha, hora, liga_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            game['id'], 
            game['teams']['home']['id'], 
            game['teams']['away']['id'], 
            date_part,  # Fecha sin modificar
            time_part,  # Hora sin el offset
            game['league']['id']
        ))

# Función principal para llenar la tabla de partidos con las próximas 15 fechas
def fill_games():
    connection = pymysql.connect(**db_config)
    
    try:
        # Empezar desde la fecha de hoy
        current_date = datetime.today()
        
        for _ in range(15):
            date_str = current_date.strftime('%Y-%m-%d')
            print(f"\nProcesando partidos para la fecha: {date_str}")
            games = get_games_by_date(date_str)
            
            for game in games:
                insert_game(connection, game)
            
            current_date += timedelta(days=1)  # Pasar al siguiente día

        connection.commit()
        print("Todos los partidos se han insertado correctamente en la base de datos.")

    except Exception as e:
        print(f"Error: {e}")
        connection.rollback()
    
    finally:
        connection.close()

# Ejecutar el script
if __name__ == "__main__":
    fill_games()
