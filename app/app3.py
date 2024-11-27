from datetime import timedelta, datetime
import bcrypt
import pymysql
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import jwt  # Para autenticación con JWT


app = FastAPI()
# Configuración de la base de datos
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

# Ruta para modificar la información del usuario
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

# Ruta para login (autenticación con JWT)
@app.post("/login")
async def login(datos: LoginRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (datos.email,))
            usuario = cursor.fetchone()
            if not usuario or not bcrypt.checkpw(datos.password.encode('utf-8'), usuario['password'].encode('utf-8')):
                raise HTTPException(status_code=401, detail="Correo electrónico o contraseña incorrectos")

            # Generar un token JWT
            token = jwt.encode({'id': usuario['id'], 'exp': datetime.utcnow() + timedelta(hours=1)}, app.config['SECRET_KEY'], algorithm='HS256')
            return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

# Ruta para recuperar contraseña
@app.post("/recuperar_contraseña")
async def recuperar_contraseña(datos: RecuperarContraseñaRequest):
    # Generar un token único para la recuperación de la contraseña
    token = str(uuid.uuid4())

    # Aquí debería ir el código para guardar el token en la base de datos asociado al usuario

    # Enviar el token por correo electrónico al usuario
    try:
        msg = MIMEMultipart()
        msg['From'] = 'tu_correo@gmail.com'
        msg['To'] = datos.email
        msg['Subject'] = 'Recuperación de Contraseña'

        body = f'Haz clic en el siguiente enlace para restablecer tu contraseña: http://localhost:5000/restablecer_contraseña/{token}'
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login('tu_correo@gmail.com', 'tu_contraseña')
            text = msg.as_string()
            server.sendmail(msg['From'], msg['To'], text)

        return {"message": "Correo enviado con el enlace para recuperar la contraseña"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo enviar el correo: {str(e)}")

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

# Rutas para obtener equipos y ligas por ID
@app.get("/equipo/{id}")
async def obtener_equipo(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM equipos WHERE id = %s", (id,))
            equipo = cursor.fetchone()
            if not equipo:
                raise HTTPException(status_code=404, detail="Equipo no encontrado")
            return equipo
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@app.get("/liga/{id}")
async def obtener_liga(id: int):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM ligas WHERE id = %s", (id,))
            liga = cursor.fetchone()
            if not liga:
                raise HTTPException(status_code=404, detail="Liga no encontrada")
            return liga
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
