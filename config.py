import os
from datetime import timedelta


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _ensure_dir(path):
    """
    Intenta crear un directorio si no existe.
    Se usa para DATA_DIR, USERS_DIR y MODELOS_DIR.
    """
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        # Si no puede crearlo, igualmente devolvemos la ruta.
        # El error real aparecerá cuando la app intente escribir.
        pass
    return path


# ==========================================================
# Directorio de datos
#
# En desarrollo local puede ser ./data.
# En Render con disco persistente puede ser /opt/data.
# ==========================================================
_DATA_DIR = os.environ.get(
    "DATA_DIR",
    os.path.join(BASE_DIR, "data")
)

_ensure_dir(_DATA_DIR)


# ==========================================================
# Dataset maestro
#
# Si el administrador sube un nuevo dataset desde el panel,
# se guarda como:
#   DATA_DIR/dataset_maestro_actual.xlsx
#
# Si ese archivo existe, se usa como dataset maestro activo.
# Si no existe, se usa la plantilla original o la variable
# de entorno ARCHIVO_DATASET.
# ==========================================================
_ARCHIVO_DATASET_SUBIDO = os.path.join(
    _DATA_DIR,
    "dataset_maestro_actual.xlsx"
)

_ARCHIVO_DATASET_DEFAULT = os.path.join(
    BASE_DIR,
    "data",
    "Plantilla_Base_Polvos_Coladores_con_ML_Dataset (version 1).xlsx"
)

# Si ya hay un dataset subido, se prioriza ese.
_ARCHIVO_DATASET = (
    _ARCHIVO_DATASET_SUBIDO
    if os.path.exists(_ARCHIVO_DATASET_SUBIDO)
    else os.environ.get(
        "ARCHIVO_DATASET",
        _ARCHIVO_DATASET_DEFAULT
    )
)


class Config:
    # ==========================================================
    # Flask
    # ==========================================================
    _SECRET_KEY_DEFAULT = "IA-Mezclas-2026-Clave-Segura-Cambiar"

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        _SECRET_KEY_DEFAULT
    )

    # Se usa en app.py para advertir en el arranque si en producción
    # seguís con la clave de ejemplo.
    SECRET_KEY_ES_DEFAULT = SECRET_KEY == _SECRET_KEY_DEFAULT

    # Por defecto DEBUG apagado.
    # Para desarrollo local usar FLASK_DEBUG=1 en .env o entorno.
    DEBUG = os.environ.get(
        "FLASK_DEBUG",
        "0"
    ) == "1"

    PERMANENT_SESSION_LIFETIME = timedelta(days=30)

    # --- Seguridad de la cookie de sesión ---
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # En producción con HTTPS debe ser 1.
    # En desarrollo local http://localhost debe ser 0.
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"

    # Límite razonable para subidas/archivos.
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    # ==========================================================
    # Directorio de datos
    # ==========================================================
    DATA_DIR = _DATA_DIR

    # ==========================================================
    # Dataset maestro
    # ==========================================================
    ARCHIVO_DATASET_SUBIDO = _ARCHIVO_DATASET_SUBIDO
    ARCHIVO_DATASET_DEFAULT = _ARCHIVO_DATASET_DEFAULT
    ARCHIVO_DATASET = _ARCHIVO_DATASET

    HOJA_DATASET = os.environ.get("HOJA_DATASET", "ML_Dataset")

    # ==========================================================
    # Modelos
    # ==========================================================
    MODELOS_DIR = _ensure_dir(os.path.join(DATA_DIR, "modelos"))

    MODELO_GLOBAL = os.path.join(
        MODELOS_DIR,
        "modelo_global.pkl"
    )

    # ==========================================================
    # Machine Learning
    # ==========================================================
    RANDOM_STATE = 42
    N_SPLITS = 5
    N_ESTIMATORS = 400

    # ==========================================================
    # Usuarios
    # ==========================================================
    USERS_DIR = _ensure_dir(os.path.join(DATA_DIR, "users"))

    # Base de usuarios.
    # Para una app chica esto alcanza; si crece, migrar a SQLite/Postgres.
    USUARIOS_DB = os.path.join(
        DATA_DIR,
        "usuarios.json"
    )

    # ==========================================================
    # Admin semilla
    # ==========================================================
    ADMIN_SEED_USUARIO = os.environ.get("ADMIN_SEED_USUARIO", "jazmin")
    ADMIN_SEED_PASSWORD = os.environ.get("ADMIN_SEED_PASSWORD", "jazmin112")

    # ==========================================================
    # Login social OAuth - Google y X
    #
    # Si no se definen estas variables, los botones no deberían
    # aparecer o deberían quedar desactivados.
    # ==========================================================
    GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    X_CLIENT_ID = os.environ.get("X_CLIENT_ID", "")
    X_CLIENT_SECRET = os.environ.get("X_CLIENT_SECRET", "")