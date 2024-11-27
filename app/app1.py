from datetime import timedelta
import datetime
import bcrypt
import pymysql
from flask import Flask, jsonify, request

# Configuración de la base de datos
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,
}

app = Flask(__name__)

# Conexión a la base de datos
def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection

# Ruta para obtener partidos
@app.route('/partidos', methods=['GET'])
def get_partidos():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM partidos"
            cursor.execute(sql)
            partidos = cursor.fetchall()

            # Imprimir los tipos de cada campo para verificar
            print(partidos)

            for partido in partidos:
                # Convertir 'hora' a string ISO
                if isinstance(partido['hora'], datetime.time):
                    partido['hora'] = partido['hora'].isoformat()

                # Convertir timedelta a segundos
                for key in partido:
                    if isinstance(partido[key], timedelta):
                        partido[key] = partido[key].total_seconds()  # Convertir a segundos

            return jsonify(partidos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener un partido específico
@app.route('/partidos/<int:id>', methods=['GET'])
def get_partido(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM partidos WHERE id = %s"
            cursor.execute(sql, (id,))
            partido = cursor.fetchone()
            if partido:
                # Obtener información del equipo local y visitante
                local_team = get_equipo(partido['id_local'])
                visitante_team = get_equipo(partido['id_visitante'])
                # Obtener información de la liga
                liga_info = get_liga(partido['liga_id'])

                # Combina la información
                partido['equipo_local'] = local_team
                partido['equipo_visitante'] = visitante_team
                partido['liga'] = liga_info

                return jsonify(partido)
            else:
                return jsonify({"error": "Partido no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener información de equipos
@app.route('/equipos/<int:id>', methods=['GET'])
def get_equipo(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM equipos WHERE id = %s"
            cursor.execute(sql, (id,))
            equipo = cursor.fetchone()
            if equipo:
                return jsonify(equipo)
            else:
                return jsonify({"error": "Equipo no encontrado"}), 404
    finally:
        connection.close()

# Ruta para obtener información de ligas
@app.route('/ligas/<int:id>', methods=['GET'])
def get_liga(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM ligas WHERE id = %s"
            cursor.execute(sql, (id,))
            liga = cursor.fetchone()
            if liga:
                return jsonify(liga)
            else:
                return jsonify({"error": "Liga no encontrada"}), 404
    finally:
        connection.close()

# Función para obtener un equipo por su ID
def get_equipo(equipo_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM equipos WHERE id = %s"
            cursor.execute(sql, (equipo_id,))
            return cursor.fetchone()
    except Exception as e:
        return {"error": str(e)}
    finally:
        connection.close()

# Función para obtener una liga por su ID
def get_liga(liga_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM ligas WHERE id = %s"
            cursor.execute(sql, (liga_id,))
            return cursor.fetchone()
    except Exception as e:
        return {"error": str(e)}
    finally:
        connection.close()


# Ruta para registrar un usuario
@app.route('/register', methods=['POST'])
def register_user():
    connection = pymysql.connect(**db_config)
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    if not username or not password or not email:
        return jsonify({"error": "Username, password and email are required"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        with connection.cursor() as cursor:
            # Verificar si el usuario ya existe
            sql_check = "SELECT COUNT(*) FROM usuarios WHERE username = %s"
            cursor.execute(sql_check, (username,))
            exists = cursor.fetchone()['COUNT(*)']

            if exists > 0:
                return jsonify({"error": "Username already exists"}), 400

            # Insertar nuevo usuario
            sql_insert = "INSERT INTO usuarios (username, password, email) VALUES (%s, %s, %s)"
            cursor.execute(sql_insert, (username, hashed_password, email))

        connection.commit()
        return jsonify({"message": "User registered successfully"}), 201

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Could not register user"}), 500

    finally:
        connection.close()


# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login_user():
    connection = pymysql.connect(**db_config)
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        with connection.cursor() as cursor:
            # Obtener el usuario de la base de datos
            sql_select = "SELECT * FROM usuarios WHERE username = %s"
            cursor.execute(sql_select, (username,))
            user = cursor.fetchone()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({"message": "Login successful", "user_id": user['id']}), 200
            else:
                return jsonify({"error": "Invalid username or password"}), 401

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Could not log in"}), 500

    finally:
        connection.close()

@app.route('/api/favoritos', methods=['POST'])
def agregar_favorito():
    data = request.json
    id_usuario = data.get("id_usuario")
    id_equipo = data.get("id_equipo")
    id_liga = data.get("id_liga")

    if not id_usuario or (not id_equipo and not id_liga):
        return jsonify({"error": "Datos incompletos"}), 400

    if id_equipo and id_liga:
        return jsonify({"error": "Solo puede enviarse id_equipo o id_liga, no ambos"}), 400

    try:
        with db.cursor() as cursor:
            # Comprueba duplicados
            cursor.execute("""
                SELECT * FROM favoritos 
                WHERE id_usuario = %s AND id_equipo = %s AND id_liga = %s
            """, (id_usuario, id_equipo, id_liga))
            if cursor.fetchone():
                return jsonify({"error": "El favorito ya existe"}), 400

            # Inserta favorito
            cursor.execute("""
                INSERT INTO favoritos (id_usuario, id_equipo, id_liga) 
                VALUES (%s, %s, %s)
            """, (id_usuario, id_equipo, id_liga))
            db.commit()
        return jsonify({"message": "Favorito agregado correctamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/usuarios/recuperar', methods=['POST'])
def recuperar_contrasena():
    data = request.json
    email = data.get('email')

    try:
        with db.cursor() as cursor:
            # Verifica que el correo exista
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Correo no encontrado"}), 404

            # Genera un token único
            token = jwt.encode({"user_id": user[0]}, SECRET_KEY, algorithm="HS256")

            # Enviar correo con el enlace (ejemplo simple)
            with SMTP("smtp.miemail.com") as smtp:
                smtp.login("miemail@miweb.com", "mi_password")
                mensaje = f"Subject: Restablecer contraseña\n\nUsa este enlace: https://miweb.com/restablecer?token={token}"
                smtp.sendmail("miemail@miweb.com", email, mensaje)

            return jsonify({"message": "Correo enviado para restablecer la contraseña"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
