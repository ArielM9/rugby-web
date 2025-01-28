from datetime import timedelta, datetime
import random
import string
import bcrypt
import pymysql
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt  # Para autenticación con JWT
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()


# Agregar el middleware CORS para permitir todos los orígenes durante el desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permite todos los encabezados
)


# accesos a la bd
#TODO: algún dia usaremos variables de entorno.
db_config = {
    'host': 'db4free.net',
    'user': 'ariel_admin',
    'password': 'quieroentrar',
    'database': 'rugby_web',
    'cursorclass': pymysql.cursors.DictCursor,
}

# app = FastAPI()

app.config = {'SECRET_KEY': 'tu_clave_secreta'}  # Cambia esto por una clave secreta real



# Modelos de datos con Pydantic
class Usuario(BaseModel):
    nombre: str
    email: str
    password: str

class UsuarioActualizado(BaseModel):
    nombre: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RecuperarContraseñaRequest(BaseModel):
    email: str

class FavoritoRequest(BaseModel):
    usuario_id: int
    favorito_id: int
    tipo: str  # 'equipo' o 'liga'
    
class EliminarFavoritoRequest(BaseModel):
    usuario_id: int
    favorito_id: int
    tipo: str  # 'equipo' o 'liga'
    #No uso un enum, porque lo valido en la función.

# Conexión a la base de datos
def get_db_connection():
    connection = pymysql.connect(**db_config)
    return connection

# Ruta para crear un usuario (registro)
@app.post("/registro")
async def crear_usuario(usuario: Usuario):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            # Comprobar si el correo ya está registrado
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (usuario.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado")

            # Encriptar la contraseña
            hashed_password = bcrypt.hashpw(usuario.password.encode('utf-8'), bcrypt.gensalt())

            # Insertar el nuevo usuario
            cursor.execute("INSERT INTO usuarios (nombre, email, password) VALUES (%s, %s, %s)",
                           (usuario.nombre, usuario.email, hashed_password))
            connection.commit()

        return {"message": "Usuario creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para obtener la información del usuario

# Ahora mismo no es una función necesaria, ya que con el login se envía esta información al frontend, 
# pero podría hacer falta en el futuro si almacenamos mas información como imágenes o alguna información extra que se considere necesaria

@app.get("/usuario/{id}")
async def obtener_usuario(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
            usuario = cursor.fetchone()
            if not usuario:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
            return usuario
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para modificar la información del usuario (tipica función de editar perfil)
@app.put("/usuario/{id}")
async def modificar_usuario(id: int, datos: UsuarioActualizado):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if datos.nombre:
                cursor.execute("UPDATE usuarios SET nombre = %s WHERE id = %s", (datos.nombre, id))
            if datos.email:
                cursor.execute("UPDATE usuarios SET email = %s WHERE id = %s", (datos.email, id))
            if datos.password:
                hashed_password = bcrypt.hashpw(datos.password.encode('utf-8'), bcrypt.gensalt())
                cursor.execute("UPDATE usuarios SET password = %s WHERE id = %s", (hashed_password, id))
            connection.commit()

        return {"message": "Usuario actualizado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para eliminar un usuario
@app.delete("/usuario/{id}")
async def eliminar_usuario(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM usuarios WHERE id = %s", (id,))
            connection.commit()

        return {"message": "Usuario eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
    #TODO: ahora mismo es posible realizar inyeccines SQL con este código, habría que darle algo mas de seguridad.

# Ruta para login
@app.post("/login")
async def login(datos: LoginRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (datos.email,))
            usuario = cursor.fetchone()
            if not usuario or not bcrypt.checkpw(datos.password.encode('utf-8'), usuario['password'].encode('utf-8')):
                raise HTTPException(status_code=401, detail="Correo electrónico o contraseña incorrectos")

            # Devuelve los datos básicos del usuario
            return {
                "id": usuario["id"],
                "email": usuario["email"],
                "nombre": usuario["nombre"]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para recuperar contraseña
@app.post("/recuperar_contraseña")
async def recuperar_contraseña(datos: RecuperarContraseñaRequest):
    email_usuario = datos.email
    nueva_password = generar_password_temporal()

    # Aquí actualizamos la contraseña en la base de datos
    try:
        conexion = get_db_connection() 
        with conexion.cursor() as cursor:
            # Verificar si el correo existe en la base de datos
            cursor.execute("SELECT id FROM usuarios WHERE correo = %s", (email_usuario,))
            usuario = cursor.fetchone()

            if not usuario:
                raise HTTPException(status_code=404, detail="Correo no registrado")

            # Actualizar la contraseña del usuario
            cursor.execute("UPDATE usuarios SET contraseña = %s WHERE correo = %s", (nueva_password, email_usuario))
            conexion.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar la contraseña: {str(e)}")

    # Enviar el correo con la nueva contraseña
    try:
        msg = MIMEMultipart()
        msg['From'] = 'correo@correo.com'
        msg['To'] = email_usuario
        msg['Subject'] = 'Recuperación de Contraseña'

        body = f'Tu nueva contraseña temporal es: {nueva_password}. Por favor, cámbiala al iniciar sesión.'
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('correo@correo.com', 'contraseña_de_mi_correo')
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)

        return {"message": "Correo enviado con la nueva contraseña"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo enviar el correo: {str(e)}")

    #TODO: Crear un mail para enviar estos correos 
    

#Función para generar una contraseña random.    
def generar_password_temporal():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))


# Ruta para crear favoritos
@app.post("/favorito")
async def crear_favorito(favorito: FavoritoRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if favorito.tipo == "equipo":
                cursor.execute(
                    "INSERT INTO favoritos (id_usuario, id_equipo, id_liga) VALUES (%s, %s, NULL)",
                    (favorito.usuario_id, favorito.favorito_id),
                )
            elif favorito.tipo == "liga":
                cursor.execute(
                    "INSERT INTO favoritos (id_usuario, id_equipo, id_liga) VALUES (%s, NULL, %s)",
                    (favorito.usuario_id, favorito.favorito_id),
                )
            else:
                raise HTTPException(status_code=400, detail="Tipo de favorito no válido")
            connection.commit()
        return {"message": "Favorito creado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# Ruta para eliminar favoritos
@app.delete("/favorito")
async def eliminar_favorito(favorito: EliminarFavoritoRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            if favorito.tipo == "equipo":
                cursor.execute(
                    "DELETE FROM favoritos WHERE id_usuario = %s AND id_equipo = %s",
                    (favorito.usuario_id, favorito.favorito_id),
                )
            elif favorito.tipo == "liga":
                cursor.execute(
                    "DELETE FROM favoritos WHERE id_usuario = %s AND id_liga = %s",
                    (favorito.usuario_id, favorito.favorito_id),
                )
            else:
                raise HTTPException(status_code=400, detail="Tipo de favorito no válido")
            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="No se encontró un favorito con los datos proporcionados",
                )
            connection.commit()
        return {"message": "Favorito eliminado exitosamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para obtener favoritos por usuario
@app.get("/favoritos/{id}")
async def obtener_favoritos(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM favoritos WHERE id_usuario = %s", (id,)
            )
            favoritos = cursor.fetchall()
            return favoritos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# Ruta para obtener los partidos de los próximos 15 días
@app.get("/partidos")
async def obtener_partidos():
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
            return partidos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para obtener partidos por ID
@app.get("/partido/{id}")
async def obtener_partido(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM partidos WHERE id = %s", (id,))
            partido = cursor.fetchone()
            if not partido:
                raise HTTPException(status_code=404, detail="Partido no encontrado")
            return partido
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para obtener equipos por ID
@app.get("/equipos")
async def obtener_equipo():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM equipos ")
            equipos = cursor.fetchall()
            if not equipos:
                raise HTTPException(status_code=404, detail="Equipo no encontrado")
            return equipos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para obtener ligas por ID
@app.get("/ligas")
async def obtener_liga():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM ligas")
            ligas = cursor.fetchall()
            if not ligas:
                raise HTTPException(status_code=404, detail="Liga no encontrada")
            return ligas
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
