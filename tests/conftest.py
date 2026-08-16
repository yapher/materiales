"""
Fixtures principales para los tests.

Proporciona:
- app: la aplicación Flask configurada para testing
- client: un cliente de test para hacer requests HTTP
- test_data_dir: un directorio temporal aislado para datos
- auth_client: un cliente autenticado como usuario normal
- admin_client: un cliente autenticado como admin
"""

import os
import json
import shutil
import tempfile
import pytest
import pandas as pd
from unittest.mock import patch

# Forzar configuración de testing ANTES de importar la app
os.environ["FLASK_DEBUG"] = "0"
os.environ["SESSION_COOKIE_SECURE"] = "0"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"


@pytest.fixture(scope="session")
def test_data_dir():
    """
    Crea un directorio temporal para aislar los datos de test
    del directorio data/ real del proyecto.
    """
    tmp_dir = tempfile.mkdtemp(prefix="mezclas_test_")

    # Crear subdirectorios esperados
    os.makedirs(os.path.join(tmp_dir, "users"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "modelos"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "tmp"), exist_ok=True)

    # Crear un dataset maestro de prueba
    _crear_dataset_test(os.path.join(tmp_dir, "dataset_maestro_actual.xlsx"))

    yield tmp_dir

    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)


def _crear_dataset_test(ruta):
    """
    Crea un archivo Excel con estructura de dataset válida para testing.
    Simula la estructura A-K (composición) + L en adelante (variables).
    """
    data = {
        # Columnas A-K: composición (*_pct)
        "CaO_pct": [40.0, 35.0, 30.0, 45.0, 38.0],
        "SiO2_pct": [30.0, 32.0, 35.0, 28.0, 31.0],
        "Al2O3_pct": [10.0, 12.0, 15.0, 8.0, 11.0],
        "MgO_pct": [5.0, 6.0, 4.0, 5.5, 6.5],
        "Na2O_pct": [3.0, 2.5, 3.5, 2.0, 2.5],
        "K2O_pct": [2.0, 2.5, 2.0, 1.5, 2.0],
        "Li2O_pct": [1.0, 1.0, 1.5, 1.0, 1.0],
        "CaF2_pct": [4.0, 4.0, 4.5, 3.0, 3.5],
        "Fe2O3_pct": [2.0, 2.0, 1.5, 2.5, 2.0],
        "MnO_pct": [1.5, 1.5, 1.0, 1.5, 1.0],
        "TiO2_pct": [1.5, 1.5, 1.5, 1.5, 1.5],
        # Columna de temperatura
        "Temperatura_C": [1500, 1550, 1600, 1450, 1520],
        # Columnas L+: variables objetivo
        "Densidad_kg_m3": [2800, 2850, 2900, 2750, 2820],
        "Viscosidad_Pa_s": [0.5, 0.6, 0.7, 0.4, 0.55],
        "Basicidad_CaO_SiO2": [1.33, 1.09, 0.86, 1.61, 1.23],
    }

    df = pd.DataFrame(data)

    # Verificar que la composición suma 100
    columnas_pct = [c for c in df.columns if c.endswith("_pct")]
    df[columnas_pct] = df[columnas_pct].div(
        df[columnas_pct].sum(axis=1), axis=0
    ).mul(100)

    df.to_excel(ruta, sheet_name="ML_Dataset", index=False)


@pytest.fixture(scope="session")
def usuarios_db_path(test_data_dir):
    """Ruta al archivo de usuarios de test."""
    return os.path.join(test_data_dir, "usuarios.json")


@pytest.fixture(scope="session")
def app(test_data_dir, usuarios_db_path):
    """
    Crea la aplicación Flask configurada para testing.
    Usa un directorio de datos temporal aislado.
    """
    with patch.dict(os.environ, {
        "DATA_DIR": test_data_dir,
        "ARCHIVO_DATASET": os.path.join(test_data_dir, "dataset_maestro_actual.xlsx"),
        "FLASK_DEBUG": "0",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "SESSION_COOKIE_SECURE": "0",
        "ADMIN_SEED_USUARIO": "testadmin",
        "ADMIN_SEED_PASSWORD": "testadmin123",
    }):
        # Necesitamos reimportar para que tome la nueva configuración
        import importlib
        import config
        importlib.reload(config)

        from app import create_app
        application = create_app()
        application.config["TESTING"] = True
        application.config["WTF_CSRF_ENABLED"] = False

        yield application


@pytest.fixture
def client(app):
    """Cliente de test para hacer requests HTTP."""
    return app.test_client()


@pytest.fixture
def auth_client(app, client, usuarios_db_path):
    """
    Cliente autenticado como usuario normal.
    Crea el usuario, hace login, y devuelve el cliente con sesión activa.
    """
    # Crear usuario de test
    _crear_usuario_test(usuarios_db_path, "testuser", "testpass123", es_admin=False)

    # Login
    client.post("/auth/login", data={
        "username": "testuser",
        "password": "testpass123",
    }, follow_redirects=True)

    yield client

    # Logout
    client.get("/auth/logout", follow_redirects=True)


@pytest.fixture
def admin_client(app, client, usuarios_db_path):
    """
    Cliente autenticado como admin.
    Crea el usuario admin, hace login, y devuelve el cliente con sesión activa.
    """
    # Crear usuario admin de test
    _crear_usuario_test(usuarios_db_path, "testadmin2", "adminpass123", es_admin=True)

    # Login
    client.post("/auth/login", data={
        "username": "testadmin2",
        "password": "adminpass123",
    }, follow_redirects=True)

    yield client

    # Logout
    client.get("/auth/logout", follow_redirects=True)


def _crear_usuario_test(db_path, username, password, es_admin=False):
    """Crea un usuario directamente en el JSON de usuarios."""
    from werkzeug.security import generate_password_hash

    usuarios = {}
    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            try:
                usuarios = json.load(f)
            except json.JSONDecodeError:
                usuarios = {}

    usuarios[username.lower()] = {
        "username": username,
        "email": f"{username}@test.com",
        "password_hash": generate_password_hash(password),
        "es_admin": es_admin,
        "proveedor": None,
        "proveedor_id": None,
    }

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)


@pytest.fixture
def sample_mix():
    """Una mezcla válida de ejemplo que suma 100%."""
    return [
        {"elemento": "CaO", "pct": 40.0},
        {"elemento": "SiO2", "pct": 30.0},
        {"elemento": "Al2O3", "pct": 10.0},
        {"elemento": "MgO", "pct": 5.0},
        {"elemento": "Na2O", "pct": 3.0},
        {"elemento": "K2O", "pct": 2.0},
        {"elemento": "Li2O", "pct": 1.0},
        {"elemento": "CaF2", "pct": 4.0},
        {"elemento": "Fe2O3", "pct": 2.0},
        {"elemento": "MnO", "pct": 1.5},
        {"elemento": "TiO2", "pct": 1.5},
    ]