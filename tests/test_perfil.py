"""
Tests unitarios para las funciones de perfil de usuario.
Verifica cambio de contraseña y actualización de datos personales.
"""
import pytest
import json
import os
from werkzeug.security import generate_password_hash

from utils.auth import (
    cambiar_password,
    actualizar_perfil,
    verificar_password,
    obtener_usuario_por_nombre,
)


@pytest.fixture
def usuario_perfil(usuarios_db_path):
    """Crea un usuario de prueba para tests de perfil."""
    usuarios = {
        "perfiluser": {
            "username": "perfiluser",
            "email": "perfil@test.com",
            "nombre": "Usuario Perfil",
            "password_hash": generate_password_hash("clave_original"),
            "es_admin": False,
            "proveedor": None,
            "proveedor_id": None,
        }
    }
    with open(usuarios_db_path, "w") as f:
        json.dump(usuarios, f)
    return "perfiluser"


class TestCambiarPassword:
    """Tests para el cambio de contraseña."""

    def test_cambio_exitoso(self, usuarios_db_path, usuario_perfil):
        """Cambiar la contraseña debe actualizar el hash."""
        cambiar_password(usuario_perfil, "nueva_clave_123")
        assert verificar_password(usuario_perfil, "nueva_clave_123") is True
        assert verificar_password(usuario_perfil, "clave_original") is False

    def test_usuario_inexistente(self, usuarios_db_path):
        """Cambiar contraseña de usuario inexistente debe lanzar error."""
        with open(usuarios_db_path, "w") as f:
            json.dump({}, f)
        with pytest.raises(ValueError):
            cambiar_password("no_existe", "nueva_clave")

    def test_usuario_social_no_tiene_password(self, usuarios_db_path):
        """Un usuario de login social no tiene password_hash."""
        usuarios = {
            "socialuser": {
                "username": "socialuser",
                "email": None,
                "password_hash": None,
                "es_admin": False,
                "proveedor": "google",
                "proveedor_id": "12345",
            }
        }
        with open(usuarios_db_path, "w") as f:
            json.dump(usuarios, f)
        # cambiar_password debería funcionar (pone un hash nuevo)
        cambiar_password("socialuser", "ahora_tiene_clave")
        assert verificar_password("socialuser", "ahora_tiene_clave") is True


class TestActualizarPerfil:
    """Tests para la actualización de datos personales."""

    def test_actualizar_email(self, usuarios_db_path, usuario_perfil):
        """Debe actualizar el email del usuario."""
        actualizar_perfil(usuario_perfil, email="nuevo@test.com")
        usuario = obtener_usuario_por_nombre(usuario_perfil)
        assert usuario["email"] == "nuevo@test.com"

    def test_actualizar_nombre(self, usuarios_db_path, usuario_perfil):
        """Debe actualizar el nombre del usuario."""
        actualizar_perfil(usuario_perfil, nombre="Nuevo Nombre")
        usuario = obtener_usuario_por_nombre(usuario_perfil)
        assert usuario["nombre"] == "Nuevo Nombre"

    def test_actualizar_ambos(self, usuarios_db_path, usuario_perfil):
        """Debe actualizar email y nombre simultáneamente."""
        actualizar_perfil(
            usuario_perfil,
            email="ambos@test.com",
            nombre="Nombre Completo",
        )
        usuario = obtener_usuario_por_nombre(usuario_perfil)
        assert usuario["email"] == "ambos@test.com"
        assert usuario["nombre"] == "Nombre Completo"

    def test_limpiar_email(self, usuarios_db_path, usuario_perfil):
        """Pasar None debe limpiar el email."""
        actualizar_perfil(usuario_perfil, email=None)
        usuario = obtener_usuario_por_nombre(usuario_perfil)
        assert usuario["email"] is None

    def test_limpiar_nombre(self, usuarios_db_path, usuario_perfil):
        """Pasar None debe limpiar el nombre."""
        actualizar_perfil(usuario_perfil, nombre=None)
        usuario = obtener_usuario_por_nombre(usuario_perfil)
        assert usuario["nombre"] is None

    def test_usuario_inexistente(self, usuarios_db_path):
        """Actualizar perfil de usuario inexistente debe lanzar error."""
        with open(usuarios_db_path, "w") as f:
            json.dump({}, f)
        with pytest.raises(ValueError):
            actualizar_perfil("no_existe", email="x@test.com")