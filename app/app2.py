from datetime import timedelta, datetime
import bcrypt
import pymysql
from flask import Flask, jsonify, request
import uuid  # Para generar un token de recuperación único
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt  # Para autenticación con JWT

# Configuración de la base de datos
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,
}

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta'  # Cambia esto por una clave secreta real

# Variable global para almacenar partidos cacheados
cache_partidos = {"data": [], "last_updated": None}

# Conexión a la base de datos
def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection

# Ruta para crear un usuario (registro)
@app.route('/registro', methods=['POST'])
def crear_usuario():
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    contraseña = data.get('contraseña')

    if not nombre or not email or not contraseña:
        return jsonify({"error": "Todos los campos son obligatorios"}), 400

    # Encriptar la contraseña
    hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())

    # Conectar a la base de datos
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Comprobar si el correo ya está registrado
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "El correo electrónico ya está registrado"}), 400
            
            # Insertar el nuevo usuario
            cursor.execute("INSERT INTO usuarios (nombre, email, contraseña) VALUES (%s, %s, %s)",
                           (nombre, email, hashed_password))
            connection.commit()

        return jsonify({"message": "Usuario creado exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener la información del usuario
@app.route('/usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            usuario = cursor.fetchone()
            if not usuario:
                return jsonify({"error": "Usuario no encontrado"}), 404
            return jsonify(usuario)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para modificar la información del usuario
@app.route('/usuario/<int:id>', methods=['PUT'])
def modificar_usuario(id):
    data = request.json
    nombre = data.get('nombre')
    email = data.get('email')
    contraseña = data.get('contraseña')

    if not nombre and not email and not contraseña:
        return jsonify({"error": "Al menos un campo debe ser proporcionado"}), 400

    # Conectar a la base de datos
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if nombre:
                cursor.execute("UPDATE usuarios SET nombre = %s WHERE id = %s", (nombre, id))
            if email:
                cursor.execute("UPDATE usuarios SET email = %s WHERE id = %s", (email, id))
            if contraseña:
                hashed_password = bcrypt.hashpw(contraseña.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("UPDATE usuarios SET contraseña = %s WHERE id = %s", (hashed_password, id))
            connection.commit()

        return jsonify({"message": "Usuario actualizado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para eliminar un usuario
@app.route('/usuario/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            connection.commit()
        return jsonify({"message": "Usuario eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para login (autenticación con JWT)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    contraseña = data.get('contraseña')

    if not email or not contraseña:
        return jsonify({"error": "El correo electrónico y la contraseña son obligatorios"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            usuario = cursor.fetchone()
            if not usuario:
                return jsonify({"error": "Correo electrónico o contraseña incorrectos"}), 401

            # Verificar la contraseña
            if not bcrypt.checkpw(contraseña.encode('utf-8'), usuario['contraseña'].encode('utf-8')):
                return jsonify({"error": "Correo electrónico o contraseña incorrectos"}), 401

            # Generar un token JWT
            token = jwt.encode({'id': usuario['id'], 'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
            return jsonify({'token': token}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para recuperar contraseña (enviando un correo con un enlace de recuperación)
@app.route('/recuperar_contraseña', methods=['POST'])
def recuperar_contraseña():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"error": "El correo electrónico es obligatorio"}), 400

    # Generar un token único para la recuperación de la contraseña
    token = str(uuid.uuid4())

    # Aquí debería ir el código para guardar el token en la base de datos asociado al usuario
    # (por ejemplo, en una tabla `recuperacion_tokens` con `email`, `token` y `fecha_expiracion`)

    # Enviar el token por correo electrónico al usuario
    try:
        msg = MIMEMultipart()
        msg['From'] = 'tu_correo@gmail.com'
        msg['To'] = email
        msg['Subject'] = 'Recuperación de Contraseña'

        body = f'Haz clic en el siguiente enlace para restablecer tu contraseña: http://localhost:5000/restablecer_contraseña/{token}'
        msg.attach(MIMEText(body, 'plain'))

        # Enviar el correo electrónico usando SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tu_correo@gmail.com', 'tu_contraseña')
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)

        return jsonify({"message": "Correo enviado con el enlace para recuperar la contraseña"}), 200
    except Exception as e:
        return jsonify({"error": f"No se pudo enviar el correo: {str(e)}"}), 500

# Ruta para crear favoritos
@app.route('/favoritos', methods=['POST'])
def crear_favoritos():
    data = request.json
    usuario_id = data.get('usuario_id')
    favoritos = data.get('favoritos')  # Lista de IDs de equipos y ligas

    if not usuario_id or not favoritos:
        return jsonify({"error": "El usuario y los favoritos son obligatorios"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            for favorito in favoritos:
                # Insertar cada favorito
                cursor.execute("INSERT INTO favoritos (usuario_id, favorito_id) VALUES (%s, %s)",
                               (usuario_id, favorito))
            connection.commit()

        return jsonify({"message": "Favoritos creados exitosamente"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para eliminar favoritos
@app.route('/favoritos', methods=['DELETE'])
def eliminar_favoritos():
    data = request.json
    usuario_id = data.get('usuario_id')
    favorito_id = data.get('favorito_id')

    if not usuario_id or not favorito_id:
        return jsonify({"error": "El usuario y el favorito son obligatorios"}), 400

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM favoritos WHERE usuario_id = %s AND favorito_id = %s", 
                           (usuario_id, favorito_id))
            connection.commit()

        return jsonify({"message": "Favorito eliminado exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener los favoritos de un usuario
@app.route('/favoritos/<int:usuario_id>', methods=['GET'])
def obtener_favoritos(usuario_id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM favoritos WHERE usuario_id = %s", (usuario_id,))
            favoritos = cursor.fetchall()
            return jsonify(favoritos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener los partidos de los próximos 15 días
@app.route('/partidos', methods=['GET'])
def obtener_partidos():
    fecha_actual = datetime.now()
    fecha_final = fecha_actual + timedelta(days=15)
    
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT * FROM partidos 
                WHERE fecha BETWEEN %s AND %s
                ORDER BY fecha ASC
            """, (fecha_actual, fecha_final))
            partidos = cursor.fetchall()
            return jsonify(partidos), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener partidos por ID
@app.route('/partido/<int:id>', methods=['GET'])
def obtener_partido(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM partidos WHERE id = %s", (id,))
            partido = cursor.fetchone()
            if not partido:
                return jsonify({"error": "Partido no encontrado"}), 404
            return jsonify(partido), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener equipos por ID
@app.route('/equipo/<int:id>', methods=['GET'])
def obtener_equipo(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM equipos WHERE id = %s", (id,))
            equipo = cursor.fetchone()
            if not equipo:
                return jsonify({"error": "Equipo no encontrado"}), 404
            return jsonify(equipo), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Ruta para obtener ligas por ID
@app.route('/liga/<int:id>', methods=['GET'])
def obtener_liga(id):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM ligas WHERE id = %s", (id,))
            liga = cursor.fetchone()
            if not liga:
                return jsonify({"error": "Liga no encontrada"}), 404
            return jsonify(liga), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()

# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
