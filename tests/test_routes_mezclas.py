"""
Tests para las rutas del módulo de mezclas/predicción.
Actualizado: dataset global, sin datasets personales.
"""
import pytest


class TestMezclasRoutes:
    """Tests para las rutas de predicción."""

    def test_index_requiere_login(self, client):
        """/mezclas debe requerir autenticación."""
        response = client.get("/mezclas", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_index_con_sesion(self, auth_client):
        """/mezclas con sesión debe devolver 200."""
        response = auth_client.get("/mezclas")
        assert response.status_code == 200

    def test_cargar_dataset_requiere_login(self, client):
        """El endpoint de cargar dataset requiere autenticación."""
        response = client.post("/mezclas/cargar_dataset")
        assert response.status_code == 401

    def test_cargar_dataset_con_sesion(self, auth_client):
        """Cargar dataset con sesión debe funcionar."""
        response = auth_client.post("/mezclas/cargar_dataset")
        assert response.status_code == 200
        data = response.get_json()
        assert "filas" in data
        assert "columnas" in data

    def test_entrenar_requiere_login(self, client):
        """El endpoint de entrenamiento requiere autenticación."""
        response = client.post("/mezclas/entrenar")
        assert response.status_code == 401

    def test_entrenar_estado_requiere_login(self, client):
        """El estado del entrenamiento requiere autenticación."""
        response = client.get("/mezclas/entrenar/estado")
        assert response.status_code == 401

    def test_estado_requiere_login(self, client):
        """El endpoint de estado general requiere autenticación."""
        response = client.get("/mezclas/estado")
        assert response.status_code == 401

    def test_predecir_requiere_login(self, client):
        """El endpoint de predicción requiere autenticación."""
        response = client.post("/mezclas/predecir")
        assert response.status_code == 401

    def test_predecir_sin_modelo(self, auth_client, sample_mix):
        """Predecir sin modelo entrenado debe dar error."""
        response = auth_client.post("/mezclas/predecir", json={
            "mix": sample_mix,
            "temperatura": 1500,
        })
        assert response.status_code in (400, 500)

    def test_dataset_view_requiere_login(self, client):
        """La vista de dataset requiere autenticación."""
        response = client.get("/mezclas/dataset", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_dataset_view_con_sesion(self, auth_client):
        """La vista de dataset con sesión debe devolver 200."""
        response = auth_client.get("/mezclas/dataset")
        assert response.status_code == 200

    def test_dataset_filas_con_sesion(self, auth_client):
        """El listado de filas del dataset debe funcionar."""
        response = auth_client.get("/mezclas/dataset/filas")
        assert response.status_code == 200
        data = response.get_json()
        assert "columnas" in data
        assert "filas" in data

    def test_ultima_prediccion_con_sesion(self, auth_client):
        """La última predicción debe devolver JSON."""
        response = auth_client.get("/mezclas/ultima_prediccion")
        assert response.status_code == 200


class TestMezclasAdmin:
    """Tests de rutas que requieren permisos de admin."""

    def test_ruta_admin_requiere_admin(self, auth_client):
        """Un usuario normal no debe poder acceder a /admin."""
        response = auth_client.get("/admin/", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_ruta_admin_con_admin(self, admin_client):
        """Un admin debe poder acceder a /admin."""
        response = admin_client.get("/admin/")
        assert response.status_code == 200