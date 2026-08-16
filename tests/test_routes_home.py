"""
Tests para las rutas de la página de inicio.
"""

import pytest


class TestHomeRoutes:
    """Tests para las rutas públicas de home."""

    def test_home_devuelve_200(self, client):
        """La página principal debe devolver 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_inicio_alias(self, client):
        """/inicio debe ser un alias de /."""
        response = client.get("/inicio")
        assert response.status_code == 200

    def test_home_contiene_titulo(self, client):
        """La página debe contener el título de la app."""
        response = client.get("/")
        assert b"Bienvenido" in response.data or b"Polvos Coladores" in response.data

    def test_healthz(self, client):
        """El endpoint de health check debe devolver ok."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"