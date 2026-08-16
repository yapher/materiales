"""
Tests para las rutas del módulo de perfil de usuario.
"""
import pytest
import io


class TestPerfilRoutes:
    """Tests para las rutas de perfil."""

    def test_perfil_requiere_login(self, client):
        """/perfil debe requerir autenticación."""
        response = client.get("/perfil/", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_perfil_con_sesion(self, auth_client):
        """/perfil con sesión debe devolver 200."""
        response = auth_client.get("/perfil/")
        assert response.status_code == 200

    def test_perfil_contiene_titulo(self, auth_client):
        """La página de perfil debe contener el título."""
        response = auth_client.get("/perfil/")
        assert b"Mi Perfil" in response.data

    def test_actualizar_datos_requiere_login(self, client):
        """Actualizar datos requiere autenticación."""
        response = client.post("/perfil/actualizar_datos")
        assert response.status_code == 401

    def test_actualizar_datos_con_sesion(self, auth_client):
        """Actualizar datos con sesión debe funcionar."""
        response = auth_client.post(
            "/perfil/actualizar_datos",
            json={"email": "nuevo@test.com", "nombre": "Test User"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_actualizar_datos_email_invalido(self, auth_client):
        """Un email inválido debe dar error."""
        response = auth_client.post(
            "/perfil/actualizar_datos",
            json={"email": "no-es-un-email"},
        )
        assert response.status_code == 400

    def test_cambiar_password_requiere_login(self, client):
        """Cambiar contraseña requiere autenticación."""
        response = client.post("/perfil/cambiar_password")
        assert response.status_code == 401

    def test_avatar_get_requiere_login(self, client):
        """Obtener avatar requiere autenticación."""
        response = client.get("/perfil/avatar")
        assert response.status_code in (301, 302, 308)

    def test_avatar_post_requiere_login(self, client):
        """Subir avatar requiere autenticación."""
        response = client.post("/perfil/avatar")
        assert response.status_code == 401

    def test_avatar_delete_requiere_login(self, client):
        """Eliminar avatar requiere autenticación."""
        response = client.delete("/perfil/avatar")
        assert response.status_code == 401


class TestPerfilPassword:
    """Tests para el cambio de contraseña vía rutas."""

    def test_cambio_password_exitoso(self, auth_client):
        """Cambio de contraseña con datos correctos."""
        response = auth_client.post(
            "/perfil/cambiar_password",
            json={
                "password_actual": "testpass123",
                "password_nueva": "nueva_clave_456",
                "password_nueva2": "nueva_clave_456",
            },
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_cambio_password_actual_incorrecta(self, auth_client):
        """Contraseña actual incorrecta debe dar error."""
        response = auth_client.post(
            "/perfil/cambiar_password",
            json={
                "password_actual": "clave_mal",
                "password_nueva": "nueva_clave_456",
                "password_nueva2": "nueva_clave_456",
            },
        )
        assert response.status_code == 400

    def test_cambio_password_nuevas_no_coinciden(self, auth_client):
        """Contraseñas nuevas distintas deben dar error."""
        response = auth_client.post(
            "/perfil/cambiar_password",
            json={
                "password_actual": "testpass123",
                "password_nueva": "clave_uno",
                "password_nueva2": "clave_dos",
            },
        )
        assert response.status_code == 400

    def test_cambio_password_corta(self, auth_client):
        """Contraseña nueva muy corta debe dar error."""
        response = auth_client.post(
            "/perfil/cambiar_password",
            json={
                "password_actual": "testpass123",
                "password_nueva": "12345",
                "password_nueva2": "12345",
            },
        )
        assert response.status_code == 400


class TestPerfilAvatar:
    """Tests para la gestión de avatar vía rutas."""

    def test_subir_avatar_extension_invalida(self, auth_client):
        """Un archivo con extensión inválida debe dar error."""
        data = {
            "avatar": (io.BytesIO(b"fake data"), "archivo.txt"),
        }
        response = auth_client.post(
            "/perfil/avatar",
            data=data,
            content_type="multipart/form-data",
        )
        assert response.status_code == 400

    def test_subir_avatar_sin_archivo(self, auth_client):
        """Subir sin archivo debe dar error."""
        response = auth_client.post("/perfil/avatar")
        assert response.status_code == 400

    def test_eliminar_avatar_sin_avatar(self, auth_client):
        """Eliminar avatar cuando no hay uno no debe dar error."""
        response = auth_client.delete("/perfil/avatar")
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True

    def test_avatar_get_sin_avatar(self, auth_client):
        """Obtener avatar sin tener uno debe dar 404."""
        response = auth_client.get("/perfil/avatar")
        assert response.status_code == 404