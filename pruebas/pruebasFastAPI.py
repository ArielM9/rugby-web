import pytest
from fastapi.testclient import TestClient
from app import app3  # Asumiendo que tu archivo principal se llama 'app.py'
from pydantic import BaseModel
import json

client = TestClient(app3)

# Modelos de entrada simulados para pruebas
class Usuario(BaseModel):
    nombre: str
    email: str
    contraseña: str

class LoginRequest(BaseModel):
    email: str
    contraseña: str

# Pruebas

@pytest.mark.asyncio
async def test_crear_usuario():
    # Datos de prueba para la creación del usuario
    usuario = {
        "nombre": "Juan Perez",
        "email": "juanperez@example.com",
        "contraseña": "mi_contraseña"
    }

    # Enviar solicitud POST para crear usuario
    response = client.post("/registro", json=usuario)

    # Verificar que la respuesta sea correcta
    assert response.status_code == 200
    assert response.json() == {"message": "Usuario creado exitosamente"}

@pytest.mark.asyncio
async def test_login_correcto():
    # Datos de prueba para login
    login_data = {
        "email": "juanperez@example.com",
        "contraseña": "mi_contraseña"
    }

    response = client.post("/login", json=login_data)

    # Verificar que el login es exitoso y contiene el token
    assert response.status_code == 200
    assert "token" in response.json()

@pytest.mark.asyncio
async def test_login_incorrecto():
    # Datos incorrectos para login
    login_data = {
        "email": "juanperez@example.com",
        "contraseña": "contraseña_incorrecta"
    }

    response = client.post("/login", json=login_data)

    # Verificar que se recibe un error 401
    assert response.status_code == 401
    assert response.json() == {"detail": "Correo electrónico o contraseña incorrectos"}

@pytest.mark.asyncio
async def test_obtener_usuario():
    # Obtener información de un usuario específico (ID 1 como ejemplo)
    response = client.get("/usuario/1")

    # Verificar que el usuario exista (asumiendo que el usuario con id 1 existe)
    assert response.status_code == 200
    assert "email" in response.json()  # Verificar que el campo 'email' esté en la respuesta

@pytest.mark.asyncio
async def test_obtener_usuario_no_existente():
    # Intentar obtener un usuario con ID no existente
    response = client.get("/usuario/9999")  # ID de un usuario no existente

    # Verificar que el código de estado sea 404
    assert response.status_code == 404
    assert response.json() == {"detail": "Usuario no encontrado"}

@pytest.mark.asyncio
async def test_modificar_usuario():
    # Datos de modificación para un usuario con ID 1
    datos_modificados = {
        "nombre": "Juanito Perez"
    }

    response = client.put("/usuario/1", json=datos_modificados)

    # Verificar que la respuesta sea la esperada
    assert response.status_code == 200
    assert response.json() == {"message": "Usuario actualizado exitosamente"}

@pytest.mark.asyncio
async def test_eliminar_usuario():
    # Eliminar un usuario con ID 1
    response = client.delete("/usuario/1")

    # Verificar que la respuesta sea exitosa
    assert response.status_code == 200
    assert response.json() == {"message": "Usuario eliminado exitosamente"}

@pytest.mark.asyncio
async def test_obtener_partidos():
    response = client.get("/partidos")

    # Verificar que la respuesta sea correcta (con partidos dentro de los próximos 15 días)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.asyncio
async def test_obtener_partido_por_id():
    response = client.get("/partido/1")

    # Verificar que el partido con ID 1 existe
    assert response.status_code == 200
    assert "fecha" in response.json()  # Verificar que el campo 'fecha' esté presente en la respuesta

@pytest.mark.asyncio
async def test_obtener_partido_no_existente():
    response = client.get("/partido/9999")

    # Verificar que el código de estado sea 404 si el partido no existe
    assert response.status_code == 404
    assert response.json() == {"detail": "Partido no encontrado"}
