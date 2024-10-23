from flask import Flask, jsonify
import pymysql
from api_client import get_countries, get_leagues, get_teams

app = Flask(__name__)

# Configuración de la base de datos
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,  # Devuelve los resultados como diccionarios
    'ssl': {'ssl': {'ca': None}}  # Para ignorar los problemas de SSL
}

# Ruta para cargar datos de la API
@app.route('/load_data')
def load_data():
    # api_key = '53bb4992e1615b3310bd9dc23b0335c4'
    try:
        teams = get_teams(api_key)
        leagues = get_leagues(api_key)
        countries = get_countries(api_key)

        # Aquí puedes insertar los datos en la base de datos
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            # Inserta equipos
            for team in teams:
                cursor.execute("INSERT INTO equipos (nombre, logo) VALUES (%s, %s)", (team['name'], team['logo']))
            
            # Inserta ligas
            for league in leagues:
                cursor.execute("INSERT INTO ligas (nombre, logo) VALUES (%s, %s)", (league['name'], league['logo']))

            # Inserta países
            for country in countries:
                cursor.execute("INSERT INTO paises (nombre, bandera) VALUES (%s, %s)", (country['name'], country['flag']))

        connection.commit()
        connection.close()
        return jsonify({"status": "success", "message": "Datos cargados exitosamente."}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
