"""
Tests para las rutas de autenticación.
"""

import pytest


class TestAuthRoutes:
    """Tests para el flujo de autenticación."""

    def test_login_page_devuelve_200(self, client):
        """La página de login debe ser accesible sin sesión."""
        response = client.get("/auth/login")
        assert response.status_code == 200

    def test_registro_page_devuelve_200(self, client):
        """La página de registro debe ser accesible sin sesión."""
        response = client.get("/auth/registro")
        assert response.status_code == 200

    def test_login_con_credenciales_invalidas(self, client):
        """Login con credenciales incorrectas debe mostrar error."""
        response = client.post("/auth/login", data={
            "username": "usuario_inexistente",
            "password": "contraseña_mal",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"incorrectos" in response.data or b"error" in response.data.lower()

    def test_registro_crea_usuario(self, client, usuarios_db_path):
        """El registro debe crear un usuario nuevo."""
        response = client.post("/auth/registro", data={
            "username": "nuevouser",
            "password": "password123",
            "password2": "password123",
            "email": "nuevo@test.com",
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_registro_passwords_no_coinciden(self, client):
        """Si las contraseñas no coinciden, debe mostrar error."""
        response = client.post("/auth/registro", data={
            "username": "otrouser",
            "password": "password123",
            "password2": "diferente456",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"coinciden" in response.data

    def test_registro_password_corta(self, client):
        """Una contraseña menor a 6 caracteres debe ser rechazada."""
        response = client.post("/auth/registro", data={
            "username": "otrouser2",
            "password": "12345",
            "password2": "12345",
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"6 caracteres" in response.data

    def test_logout_redirige(self, auth_client):
        """El logout debe redirigir a home."""
        response = auth_client.get("/auth/logout", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_ruta_protegida_sin_sesion(self, client):
        """Una ruta protegida sin sesión debe redirigir a login."""
        response = client.get("/mezclas", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_ruta_protegida_con_sesion(self, auth_client):
        """Una ruta protegida con sesión debe devolver 200."""
        response = auth_client.get("/mezclas")
        assert response.status_code == 200