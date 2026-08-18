"""
Tests para las rutas del panel de administración.
Actualizado para la arquitectura de dataset global único.
"""
import pytest
import os
import io
import json


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

    def test_admin_dataset_redirige_a_dataset_global(self, admin_client):
        """
        La vista /admin/dataset ahora redirige a /mezclas/dataset
        (dataset global unificado).
        """
        response = admin_client.get("/admin/dataset", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_admin_dataset_sigue_redirect(self, admin_client):
        """
        Siguiendo el redirect de /admin/dataset se llega a
        /mezclas/dataset con 200.
        """
        response = admin_client.get("/admin/dataset", follow_redirects=True)
        assert response.status_code == 200
        assert b"Dataset" in response.data

    def test_admin_accede_a_filas_desde_mezclas(self, admin_client):
        """
        Las filas del dataset ahora se acceden desde
        /mezclas/dataset/filas (ya no desde /admin/dataset/filas).
        """
        response = admin_client.get("/mezclas/dataset/filas")
        assert response.status_code == 200
        data = response.get_json()
        assert "columnas" in data
        assert "filas" in data
        assert data["es_admin"] is True

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


class TestAdminSubirDatasetPropagacion:
    """
    Tests para verificar que subir un dataset afecta a todos los usuarios.
    
    IMPORTANTE: Este test usa SOLO admin_client.
    NO se puede usar auth_client + admin_client juntos porque
    ambos comparten el mismo cliente HTTP y se pisan la sesión.
    """

    def test_subir_dataset_borra_modelos_de_todos(
        self, admin_client, test_data_dir
    ):
        """
        Al subir un nuevo dataset maestro:
        - Se reemplaza el dataset global
        - Se borran los modelos de todos los usuarios
        """
        import os
        import io
        import json
        import pandas as pd

        # ==========================================================
        # PASO 1: Crear un modelo fake para "testuser"
        # (simula un usuario que ya había entrenado)
        # ==========================================================
        carpeta_user = os.path.join(test_data_dir, "users", "testuser")
        os.makedirs(carpeta_user, exist_ok=True)
        modelo_fake = os.path.join(carpeta_user, "modelo.pkl")
        info_fake = os.path.join(carpeta_user, "info_modelo.json")

        with open(modelo_fake, "wb") as f:
            f.write(b"fake_model_data")
        with open(info_fake, "w") as f:
            json.dump({"entrenado": True}, f)

        assert os.path.exists(modelo_fake)
        assert os.path.exists(info_fake)

        # ==========================================================
        # PASO 2: Crear archivo Excel de prueba para subir
        # ==========================================================
        data = {
            "CaO_pct": [40.0, 35.0, 30.0],
            "SiO2_pct": [30.0, 32.0, 35.0],
            "Al2O3_pct": [10.0, 12.0, 15.0],
            "MgO_pct": [5.0, 6.0, 4.0],
            "Na2O_pct": [3.0, 2.5, 3.5],
            "K2O_pct": [2.0, 2.5, 2.0],
            "Li2O_pct": [1.0, 1.0, 1.5],
            "CaF2_pct": [4.0, 4.0, 4.5],
            "Fe2O3_pct": [2.0, 2.0, 1.5],
            "MnO_pct": [1.5, 1.5, 1.0],
            "TiO2_pct": [1.5, 1.5, 1.5],
            "Temperatura_C": [1500, 1550, 1600],
            "Densidad_kg_m3": [2800, 2850, 2900],
        }
        df = pd.DataFrame(data)
        columnas_pct = [c for c in df.columns if c.endswith("_pct")]
        df[columnas_pct] = (
            df[columnas_pct]
            .div(df[columnas_pct].sum(axis=1), axis=0)
            .mul(100)
        )

        buffer = io.BytesIO()
        df.to_excel(buffer, sheet_name="ML_Dataset", index=False)
        buffer.seek(0)

        # ==========================================================
        # PASO 3: Subir dataset como admin
        # ==========================================================
        response = admin_client.post(
            "/admin/subir_dataset",
            data={"archivo": (buffer, "nuevo_dataset.xlsx")},
            content_type="multipart/form-data",
        )
        assert response.status_code == 200, (
            f"Se esperaba 200 pero se obtuvo {response.status_code}. "
            f"Respuesta: {response.get_data(as_text=True)}"
        )
        data_resp = response.get_json()
        assert data_resp["ok"] is True
        assert data_resp["usuarios_actualizados"] >= 1
        assert data_resp["modelos_borrados"] >= 1

        # ==========================================================
        # PASO 4: Verificar que el modelo de "testuser" fue borrado
        # ==========================================================
        assert not os.path.exists(modelo_fake), (
            "El modelo del usuario debería haber sido borrado "
            "al subir el nuevo dataset"
        )
        assert not os.path.exists(info_fake), (
            "El info_modelo.json debería haber sido borrado "
            "al subir el nuevo dataset"
        )

        # ==========================================================
        # PASO 5: Verificar que el dataset global tiene 3 filas
        # ==========================================================
        response = admin_client.get("/mezclas/dataset/filas")
        assert response.status_code == 200
        data_filas = response.get_json()
        assert "columnas" in data_filas
        assert "filas" in data_filas
        assert len(data_filas["filas"]) == 3, (
            f"Se esperaban 3 filas del nuevo dataset, "
            f"pero se obtuvieron {len(data_filas['filas'])}"
        )