"""
Tests para utils/auth.py.
Verifica creación de usuarios, verificación de contraseñas y roles.
"""

import pytest
import json
import os
from utils.auth import (
    validar_username,
    verificar_password,
    obtener_usuario_por_nombre,
)


class TestValidarUsername:
    """Tests para la validación de nombres de usuario."""

    def test_username_valido(self):
        valido, error = validar_username("usuario1")
        assert valido is True
        assert error is None

    def test_username_con_guion(self):
        valido, error = validar_username("mi-usuario")
        assert valido is True

    def test_username_con_guion_bajo(self):
        valido, error = validar_username("mi_usuario")
        assert valido is True

    def test_username_muy_corto(self):
        valido, error = validar_username("ab")
        assert valido is False
        assert error is not None

    def test_username_muy_largo(self):
        valido, error = validar_username("a" * 31)
        assert valido is False

    def test_username_con_espacios(self):
        valido, error = validar_username("mi usuario")
        assert valido is False

    def test_username_con_caracteres_especiales(self):
        valido, error = validar_username("user@name!")
        assert valido is False

    def test_username_none(self):
        valido, error = validar_username(None)
        assert valido is False

    def test_username_vacio(self):
        valido, error = validar_username("")
        assert valido is False


class TestVerificarPassword:
    """Tests para la verificación de contraseñas."""

    def test_password_correcta(self, usuarios_db_path):
        """Verificar que una contraseña correcta pasa."""
        from werkzeug.security import generate_password_hash

        # Crear usuario directamente
        usuarios = {
            "testpass": {
                "username": "testpass",
                "email": None,
                "password_hash": generate_password_hash("mipass123"),
                "es_admin": False,
                "proveedor": None,
                "proveedor_id": None,
            }
        }
        with open(usuarios_db_path, "w") as f:
            json.dump(usuarios, f)

        assert verificar_password("testpass", "mipass123") is True

    def test_password_incorrecta(self, usuarios_db_path):
        """Verificar que una contraseña incorrecta falla."""
        from werkzeug.security import generate_password_hash

        usuarios = {
            "testpass2": {
                "username": "testpass2",
                "email": None,
                "password_hash": generate_password_hash("mipass123"),
                "es_admin": False,
                "proveedor": None,
                "proveedor_id": None,
            }
        }
        with open(usuarios_db_path, "w") as f:
            json.dump(usuarios, f)

        assert verificar_password("testpass2", "contraseña_mal") is False

    def test_usuario_inexistente(self, usuarios_db_path):
        """Un usuario que no existe debe fallar."""
        with open(usuarios_db_path, "w") as f:
            json.dump({}, f)

        assert verificar_password("no_existe", "cualquiera") is False

    def test_usuario_social_sin_password(self, usuarios_db_path):
        """Un usuario social (sin password_hash) debe fallar con password."""
        usuarios = {
            "socialuser": {
                "username": "socialuser",
                "email": "social@google.com",
                "password_hash": None,
                "es_admin": False,
                "proveedor": "google",
                "proveedor_id": "12345",
            }
        }
        with open(usuarios_db_path, "w") as f:
            json.dump(usuarios, f)

        assert verificar_password("socialuser", "cualquiera") is False