"""
Fixtures principales para los tests.
Correcciones clave:
- Usa un directorio DATA_DIR temporal.
- Parchea Config.USUARIOS_DB antes de importar/crear la app.
- Crea un dataset maestro Excel temporal válido.
- Los usuarios de prueba se crean realmente en el usuarios.json temporal.
- El login se verifica mediante el redirect 302.
"""
import os
import json
import shutil
import tempfile
import pytest
import pandas as pd
from config import Config
from werkzeug.security import generate_password_hash


# ==========================================================
# DIRECTORIO TEMPORAL DE DATOS
# ==========================================================

@pytest.fixture(scope="session")
def test_data_dir():
    """
    Crea un directorio temporal para aislar completamente los datos
    de test del directorio data/ real del proyecto.
    """
    tmp_dir = tempfile.mkdtemp(prefix="mezclas_test_")
    os.makedirs(os.path.join(tmp_dir, "users"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "modelos"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "backups"), exist_ok=True)
    os.makedirs(os.path.join(tmp_dir, "tmp"), exist_ok=True)

    # Crear dataset maestro de prueba
    dataset_path = os.path.join(
        tmp_dir,
        "dataset_maestro_actual.xlsx"
    )
    _crear_dataset_test(dataset_path)

    yield tmp_dir

    shutil.rmtree(tmp_dir, ignore_errors=True)


def _crear_dataset_test(ruta):
    """
    Crea un archivo Excel con estructura de dataset válida para testing.
    Estructura:
    - Columnas 1 a 11: composición (*_pct)
    - Columna 12: temperatura
    - Columnas siguientes: variables objetivo
    """
    data = {
        # Composición
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
        # Temperatura
        "Temperatura_C": [1500, 1550, 1600, 1450, 1520],
        # Variables objetivo
        "Densidad_kg_m3": [2800, 2850, 2900, 2750, 2820],
        "Viscosidad_Pa_s": [0.5, 0.6, 0.7, 0.4, 0.55],
        "Basicidad_CaO_SiO2": [1.33, 1.09, 0.86, 1.61, 1.23],
    }
    df = pd.DataFrame(data)

    # Normalizar composición para que sume 100 en cada fila
    columnas_pct = [c for c in df.columns if c.endswith("_pct")]
    df[columnas_pct] = (
        df[columnas_pct]
        .div(df[columnas_pct].sum(axis=1), axis=0)
        .mul(100)
    )

    df.to_excel(
        ruta,
        sheet_name="ML_Dataset",
        index=False
    )


# ==========================================================
# ARCHIVO DE USUARIOS TEMPORAL
# ==========================================================

@pytest.fixture(scope="session")
def usuarios_db_path(test_data_dir):
    """
    Ruta al archivo de usuarios temporal.
    """
    return os.path.join(test_data_dir, "usuarios.json")


# ==========================================================
# PARCHEO GLOBAL DE CONFIG
# ==========================================================

@pytest.fixture(scope="session", autouse=True)
def patch_config_for_tests(test_data_dir, usuarios_db_path):
    """
    Parchea Config antes de que la app y los servicios usen rutas reales.
    Esto es clave para que:
    - utils.auth lea el usuarios.json temporal
    - los datasets se guarden en el DATA_DIR temporal
    - los modelos se guarden en el MODELOS_DIR temporal
    """
    originales = {}
    nuevos_valores = {
        "DATA_DIR": test_data_dir,
        "USUARIOS_DB": usuarios_db_path,
        "USERS_DIR": os.path.join(
            test_data_dir,
            "users"
        ),
        "MODELOS_DIR": os.path.join(
            test_data_dir,
            "modelos"
        ),
        "ARCHIVO_DATASET_SUBIDO": os.path.join(
            test_data_dir,
            "dataset_maestro_actual.xlsx"
        ),
        "ARCHIVO_DATASET": os.path.join(
            test_data_dir,
            "dataset_maestro_actual.xlsx"
        ),
        "ARCHIVO_DATASET_DEFAULT": os.path.join(
            test_data_dir,
            "dataset_maestro_actual.xlsx"
        ),
        "HOJA_DATASET": "ML_Dataset",
        "SECRET_KEY": "test-secret-key-for-testing-only",
        "SECRET_KEY_ES_DEFAULT": False,
        "DEBUG": False,
        "SESSION_COOKIE_SECURE": False,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "ADMIN_SEED_USUARIO": "testadminseed",
        "ADMIN_SEED_PASSWORD": "testadminseed123",
    }

    for clave, valor in nuevos_valores.items():
        originales[clave] = getattr(Config, clave, None)
        setattr(Config, clave, valor)

    yield

    # Restaurar valores originales
    for clave, valor in originales.items():
        setattr(Config, clave, valor)


# ==========================================================
# APP FLASK DE TEST
# ==========================================================

@pytest.fixture(scope="session")
def app(patch_config_for_tests):
    """
    Crea la aplicación Flask configurada para testing.
    IMPORTANTE:
    Se importa app recién acá, después de parchear Config.
    """
    import app as app_module

    # app.py define create_app() y también una instancia global app.
    # Usamos create_app() para obtener una app limpia de test.
    application = app_module.create_app()
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
        SECRET_KEY=Config.SECRET_KEY,
        SESSION_COOKIE_SECURE=False,
    )
    yield application


# ==========================================================
# CLIENTE HTTP
# ==========================================================

@pytest.fixture
def client(app):
    """
    Cliente de test para hacer requests HTTP.
    """
    return app.test_client()


# ==========================================================
# HELPERS DE USUARIOS
# ==========================================================

def _crear_usuario_test(
    db_path,
    username,
    password,
    es_admin=False,
    nombre=None,
):
    """
    Crea o actualiza un usuario directamente en el JSON de usuarios
    temporal usado por los tests.
    """
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    usuarios = {}
    if os.path.exists(db_path):
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
        except Exception:
            usuarios = {}

    usuarios[username.lower()] = {
        "username": username,
        "email": f"{username}@test.com",
        "nombre": nombre,
        "password_hash": generate_password_hash(password),
        "es_admin": es_admin,
        "proveedor": None,
        "proveedor_id": None,
    }

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)


def _login_usuario(client, username, password):
    """
    Hace login y verifica que la respuesta sea un redirect.
    Si el login falla, la respuesta sería 200 mostrando nuevamente
    el formulario con un error, no un redirect.
    """
    response = client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
        follow_redirects=False,
    )
    assert response.status_code in (301, 302, 308), (
        f"Login falló para {username}. "
        f"Status: {response.status_code}"
    )
    return response


# ==========================================================
# CLIENTE AUTENTICADO COMO USUARIO NORMAL
# ==========================================================

@pytest.fixture
def auth_client(app, client, usuarios_db_path):
    """
    Cliente autenticado como usuario normal.
    """
    _crear_usuario_test(
        usuarios_db_path,
        "testuser",
        "testpass123",
        es_admin=False,
        nombre="Test User",
    )
    _login_usuario(
        client,
        "testuser",
        "testpass123",
    )
    yield client
    client.get(
        "/auth/logout",
        follow_redirects=False,
    )


# ==========================================================
# CLIENTE AUTENTICADO COMO ADMIN
# ==========================================================

@pytest.fixture
def admin_client(app, client, usuarios_db_path):
    """
    Cliente autenticado como admin.
    """
    _crear_usuario_test(
        usuarios_db_path,
        "testadmin2",
        "adminpass123",
        es_admin=True,
        nombre="Test Admin",
    )
    _login_usuario(
        client,
        "testadmin2",
        "adminpass123",
    )
    yield client
    client.get(
        "/auth/logout",
        follow_redirects=False,
    )


# ==========================================================
# DATOS DE EJEMPLO
# ==========================================================

@pytest.fixture
def sample_mix():
    """
    Una mezcla válida de ejemplo que suma 100%.
    """
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