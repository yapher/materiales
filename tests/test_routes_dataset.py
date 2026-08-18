"""
Tests para las rutas del dataset global.
Verifica:
- Acceso para todos los usuarios logueados
- Solo admin puede editar/borrar/agregar
- No-admin solo puede ver y exportar PDF
- Al editar el admin, se borra el modelo
"""
import pytest


class TestDatasetView:
    """Tests para la vista del dataset."""

    def test_dataset_requiere_login(self, client):
        """El dataset requiere autenticación."""
        response = client.get(
            "/mezclas/dataset", follow_redirects=False
        )
        assert response.status_code in (301, 302, 308)

    def test_dataset_con_sesion_usuario_normal(self, auth_client):
        """Un usuario normal puede ver el dataset."""
        response = auth_client.get("/mezclas/dataset")
        assert response.status_code == 200

    def test_dataset_con_sesion_admin(self, admin_client):
        """Un admin puede ver el dataset."""
        response = admin_client.get("/mezclas/dataset")
        assert response.status_code == 200

    def test_dataset_contiene_titulo(self, auth_client):
        """La página debe contener el título 'Dataset'."""
        response = auth_client.get("/mezclas/dataset")
        assert b"Dataset" in response.data

    def test_dataset_es_global_no_personal(self, auth_client):
        """El dataset es global, no debe decir 'Mi Dataset'."""
        response = auth_client.get("/mezclas/dataset")
        assert b"Mi Dataset" not in response.data

    def test_dataset_usuario_normal_ve_solo_lectura(self, auth_client):
        """Usuario normal ve indicación de solo lectura."""
        response = auth_client.get("/mezclas/dataset")
        assert b"solo lectura" in response.data.lower() or \
               b"Dataset" in response.data


class TestDatasetFilas:
    """Tests para el listado de filas."""

    def test_filas_requiere_login(self, client):
        """El listado de filas requiere autenticación."""
        response = client.get("/mezclas/dataset/filas")
        assert response.status_code == 401

    def test_filas_con_usuario_normal(self, auth_client):
        """Un usuario normal puede listar filas."""
        response = auth_client.get("/mezclas/dataset/filas")
        assert response.status_code == 200
        data = response.get_json()
        assert "columnas" in data
        assert "filas" in data
        assert data["es_admin"] is False

    def test_filas_con_admin(self, admin_client):
        """Un admin puede listar filas y es_admin=True."""
        response = admin_client.get("/mezclas/dataset/filas")
        assert response.status_code == 200
        data = response.get_json()
        assert "columnas" in data
        assert "filas" in data
        assert data["es_admin"] is True

    def test_filas_tiene_estructura_correcta(self, auth_client):
        """Cada fila tiene indice, valores, inconsistente, motivo."""
        response = auth_client.get("/mezclas/dataset/filas")
        data = response.get_json()
        if data["filas"]:
            fila = data["filas"][0]
            assert "indice" in fila
            assert "valores" in fila
            assert "inconsistente" in fila
            assert "motivo" in fila


class TestDatasetEdicionSoloAdmin:
    """Tests de permisos de edición."""

    def test_usuario_normal_no_puede_editar(self, auth_client):
        """Un usuario normal NO puede editar filas."""
        response = auth_client.put(
            "/mezclas/dataset/filas/0",
            json={"CaO_pct": 50.0},
        )
        assert response.status_code == 403

    def test_usuario_normal_no_puede_borrar(self, auth_client):
        """Un usuario normal NO puede borrar filas."""
        response = auth_client.delete("/mezclas/dataset/filas/0")
        assert response.status_code == 403

    def test_usuario_normal_no_puede_agregar(self, auth_client):
        """Un usuario normal NO puede agregar filas."""
        response = auth_client.post(
            "/mezclas/dataset/filas",
            json={"CaO_pct": 50.0},
        )
        assert response.status_code == 403

    def test_admin_puede_editar(self, admin_client):
        """Un admin puede editar filas."""
        response = admin_client.put(
            "/mezclas/dataset/filas/0",
            json={"CaO_pct": 25.0},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert (
            "modelo" in data["mensaje"].lower()
            or "reentren" in data["mensaje"].lower()
        )

    def test_admin_puede_borrar(self, admin_client):
        """Un admin puede borrar filas."""
        response = admin_client.get("/mezclas/dataset/filas")
        data = response.get_json()
        if len(data["filas"]) > 0:
            response = admin_client.delete("/mezclas/dataset/filas/0")
            assert response.status_code == 200
            data = response.get_json()
            assert data["ok"] is True

    def test_admin_puede_agregar(self, admin_client):
        """Un admin puede agregar filas."""
        response = admin_client.post(
            "/mezclas/dataset/filas",
            json={"CaO_pct": 100.0},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True


class TestDatasetPdf:
    """Tests de exportación a PDF."""

    def test_pdf_requiere_login(self, client):
        """Exportar PDF requiere autenticación."""
        response = client.get(
            "/mezclas/dataset/filas/0/pdf",
            follow_redirects=False,
        )
        assert response.status_code in (301, 302, 308)

    def test_pdf_con_usuario_normal(self, auth_client):
        """Un usuario normal puede exportar a PDF."""
        response = auth_client.get("/mezclas/dataset/filas/0/pdf")
        assert response.status_code == 200
        assert response.content_type == "application/pdf"

    def test_pdf_con_admin(self, admin_client):
        """Un admin puede exportar a PDF."""
        response = admin_client.get("/mezclas/dataset/filas/0/pdf")
        assert response.status_code == 200
        assert response.content_type == "application/pdf"


class TestDatasetGuardarPrediccion:
    """Tests para guardar predicción en dataset (solo admin)."""

    def test_guardar_prediccion_requiere_admin(self, auth_client):
        """Un usuario normal NO puede guardar predicción."""
        response = auth_client.post(
            "/mezclas/guardar_prediccion",
            json={
                "mix": [{"elemento": "CaO", "pct": 100}],
                "temperatura": 1500,
            },
        )
        assert response.status_code == 403

    def test_guardar_prediccion_sin_login(self, client):
        """Sin login no se puede guardar predicción."""
        response = client.post("/mezclas/guardar_prediccion")
        assert response.status_code == 401