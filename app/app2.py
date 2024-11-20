from flask import Flask, request, jsonify
import pymysql

# Inicializamos la aplicación Flask
app = Flask(__name__)

# Función para obtener la conexión a la base de datos
def get_db_connection():
    """Establece la conexión a la base de datos MySQL."""
    connection = pymysql.connect(
        host='sql310.infinityfree.com',  # Dirección del servidor de la base de datos
        user='usuario',  # Reemplaza con tu usuario de MySQL
        password='contraseña',  # Reemplaza con tu contraseña de MySQL
        database='mi_base_de_datos'  # Reemplaza con el nombre de tu base de datos
    )
    return connection

# Función para validar la entrada de datos en las solicitudes
def validate_inputs(data, required_fields):
    """Valida que los campos requeridos estén presentes y no vacíos."""
    for field in required_fields:
        if field not in data or not data[field]:
            return f"El campo {field} es obligatorio."
    return None

# Ruta para obtener partidos desde la base de datos, filtrados por fecha
@app.route('/api/partidos', methods=['GET'])
def obtener_partidos():
    """Obtiene los partidos de la base de datos, ordenados por fecha."""
    fecha = request.args.get('fecha')  # Obtenemos la fecha como parámetro de consulta
    if not fecha:
        return jsonify({'error': 'El parámetro "fecha" es obligatorio.'}), 400

    # Verificar que la fecha tenga el formato correcto (YYYY-MM-DD)
    if not fecha.isdigit() or len(fecha) != 10 or fecha[4] != '-' or fecha[7] != '-':
        return jsonify({'error': 'El formato de la fecha es incorrecto. Use YYYY-MM-DD.'}), 400

    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Realizamos la consulta para obtener los partidos desde la fecha proporcionada
            query = """
                SELECT * FROM partidos 
                WHERE fecha >= %s
                ORDER BY fecha ASC, hora ASC
            """
            cursor.execute(query, (fecha,))
            partidos = cursor.fetchall()

        if partidos:
            return jsonify(partidos), 200  # Devolvemos los partidos encontrados
        else:
            return jsonify({'message': 'No se encontraron partidos para esta fecha.'}), 404  # Si no hay partidos

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # En caso de error
    finally:
        connection.close()  # Cerramos la conexión

# Ruta para registrar un nuevo usuario en la base de datos
@app.route('/api/registro', methods=['POST'])
def registro():
    """Registra un nuevo usuario en la base de datos."""
    data = request.json  # Obtenemos los datos del cuerpo de la solicitud
    error = validate_inputs(data, ['nombre', 'email', 'password'])  # Validamos los campos requeridos
    if error:
        return jsonify({'error': error}), 400  # Si hay un error, respondemos con un código 400

    nombre = data['nombre']
    email = data['email']
    password = data['password']

    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Insertamos los datos del nuevo usuario en la tabla 'usuarios'
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                (nombre, email, password)
            )
            connection.commit()  # Confirmamos la transacción

        return jsonify({'message': 'Usuario registrado con éxito.'}), 201  # Respuesta exitosa

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Si ocurre un error

    finally:
        connection.close()  # Cerramos la conexión

# Ruta para iniciar sesión de un usuario, validando sus credenciales
@app.route('/api/login', methods=['POST'])
def login():
    """Verifica las credenciales de un usuario para iniciar sesión."""
    data = request.json
    error = validate_inputs(data, ['email', 'password'])  # Validamos los campos requeridos
    if error:
        return jsonify({'error': error}), 400  # Si hay un error, respondemos con un código 400

    email = data['email']
    password = data['password']

    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Consultamos la base de datos para verificar las credenciales
            cursor.execute("SELECT * FROM usuarios WHERE email = %s AND password = %s", (email, password))
            usuario = cursor.fetchone()  # Obtenemos el primer resultado

        if usuario:
            return jsonify({'message': 'Inicio de sesión exitoso.'}), 200  # Si las credenciales son correctas
        else:
            return jsonify({'error': 'Credenciales inválidas.'}), 401  # Si las credenciales son incorrectas

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Si ocurre un error

    finally:
        connection.close()  # Cerramos la conexión

# Ruta para obtener los detalles de un usuario por su ID
@app.route('/api/usuario/<int:id>', methods=['GET'])
def obtener_usuario(id):
    """Obtiene los detalles de un usuario por su ID."""
    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # Consultamos los datos del usuario con el ID proporcionado
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            usuario = cursor.fetchone()

        if usuario:
            return jsonify(usuario), 200  # Devolvemos los detalles del usuario
        else:
            return jsonify({'message': 'Usuario no encontrado.'}), 404  # Si no se encuentra el usuario

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Si ocurre un error

    finally:
        connection.close()  # Cerramos la conexión

# Ruta para actualizar los datos de un usuario
@app.route('/api/usuario/<int:id>', methods=['PUT'])
def actualizar_usuario(id):
    """Actualiza los datos de un usuario específico."""
    data = request.json  # Obtenemos los datos del cuerpo de la solicitud
    error = validate_inputs(data, ['nombre', 'email'])  # Validamos los campos requeridos
    if error:
        return jsonify({'error': error}), 400  # Si hay un error, respondemos con un código 400

    nombre = data['nombre']
    email = data['email']

    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Actualizamos los datos del usuario con el ID proporcionado
            cursor.execute(
                "UPDATE usuarios SET nombre = %s, email = %s WHERE id = %s",
                (nombre, email, id)
            )
            connection.commit()  # Confirmamos la transacción

        return jsonify({'message': 'Usuario actualizado con éxito.'}), 200  # Respuesta exitosa

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Si ocurre un error

    finally:
        connection.close()  # Cerramos la conexión

# Ruta para eliminar un usuario de la base de datos
@app.route('/api/usuario/<int:id>', methods=['DELETE'])
def eliminar_usuario(id):
    """Elimina un usuario de la base de datos."""
    try:
        # Abrimos la conexión a la base de datos
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Eliminamos el usuario con el ID proporcionado
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            connection.commit()  # Confirmamos la transacción

        return jsonify({'message': 'Usuario eliminado con éxito.'}), 200  # Respuesta exitosa

    except Exception as e:
        return jsonify({'error': str(e)}), 500  # Si ocurre un error

    finally:
        connection.close()  # Cerramos la conexión

# Inicia la aplicación Flask
if __name__ == '__main__':
    app.run(debug=True)
