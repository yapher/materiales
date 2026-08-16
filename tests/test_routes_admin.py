"""
Tests para las rutas del panel de administración.
"""

import pytest


class TestAdminRoutes:
    """Tests para las rutas de administración."""

    def test_admin_index_requiere_login(self, client):
        """El panel de admin requiere autenticación."""
        response = client.get("/admin/", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_admin_index_requiere_admin(self, auth_client):
        """Un usuario normal no puede acceder al panel de admin."""
        response = auth_client.get("/admin/", follow_redirects=False)
        # Redirige porque no es admin
        assert response.status_code in (301, 302, 308)

    def test_admin_index_con_admin(self, admin_client):
        """Un admin puede acceder al panel."""
        response = admin_client.get("/admin/")
        assert response.status_code == 200

    def test_admin_estado_con_admin(self, admin_client):
        """El endpoint de estado funciona para admin."""
        response = admin_client.get("/admin/estado")
        assert response.status_code == 200
        data = response.get_json()
        assert "usuario" in data
        assert "dataset_cargado" in data

    def test_admin_estado_requiere_admin(self, auth_client):
        """El estado de admin no es accesible para usuarios normales."""
        response = auth_client.get("/admin/estado")
        assert response.status_code == 403

    def test_admin_dataset_con_admin(self, admin_client):
        """La vista de dataset maestro funciona para admin."""
        response = admin_client.get("/admin/dataset")
        assert response.status_code == 200

    def test_admin_dataset_filas_con_admin(self, admin_client):
        """El listado de filas del dataset maestro funciona."""
        response = admin_client.get("/admin/dataset/filas")
        assert response.status_code == 200
        data = response.get_json()
        assert "columnas" in data
        assert "filas" in data

    def test_admin_usuarios_con_admin(self, admin_client):
        """La vista de usuarios funciona para admin."""
        response = admin_client.get("/admin/usuarios")
        assert response.status_code == 200

    def test_admin_usuarios_lista_con_admin(self, admin_client):
        """El listado de usuarios funciona para admin."""
        response = admin_client.get("/admin/usuarios/lista")
        assert response.status_code == 200
        data = response.get_json()
        assert "usuarios" in data
        assert "usuario_actual" in data

    def test_admin_reset_modelo_requiere_admin(self, auth_client):
        """El reset de modelo no es accesible para usuarios normales."""
        response = auth_client.post("/admin/reset_modelo")
        assert response.status_code == 403

    def test_admin_recargar_dataset_requiere_admin(self, auth_client):
        """La recarga de dataset no es accesible para usuarios normales."""
        response = auth_client.post("/admin/recargar_dataset")
        assert response.status_code == 403


class TestAdminSeguridad:
    """Tests de seguridad del panel de administración."""

    def test_usuario_normal_no_puede_ver_usuarios(self, auth_client):
        """Un usuario normal no puede listar usuarios."""
        response = auth_client.get("/admin/usuarios/lista")
        assert response.status_code == 403

    def test_sin_sesion_no_puede_ver_usuarios(self, client):
        """Sin sesión no se puede acceder a la lista de usuarios."""
        response = client.get("/admin/usuarios/lista")
        assert response.status_code == 401

    def test_sin_sesion_no_puede_reset_modelo(self, client):
        """Sin sesión no se puede resetear el modelo."""
        response = client.post("/admin/reset_modelo")
        assert response.status_code == 401