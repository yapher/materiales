"""
Persistencia del modelo entrenado.

Responsabilidades:
- cargar modelo.pkl a memoria
- guardar modelo.pkl
- borrar modelo.pkl e info_modelo.json
"""

import os
import logging

import joblib

from utils import (
    archivo_modelo_usuario,
    archivo_info_usuario,
)

from .state import (
    obtener_usuario,
    _modelos,
    _lock_global,
    _lock_estado,
    _estado_entrenamiento,
)


logger = logging.getLogger(__name__)


def cargar_modelo():
    """
    Carga el modelo persistido del usuario actual, si existe.
    """
    user_id = obtener_usuario()
    ruta = archivo_modelo_usuario()

    if _modelos[user_id] is None and os.path.exists(ruta):
        logger.info(
            "Cargando modelo persistido del usuario %s",
            user_id
        )

        _modelos[user_id] = joblib.load(ruta)

    return _modelos[user_id]


def _guardar_modelo(user_id, modelos):
    """
    Guarda el diccionario de modelos del usuario en disco.
    """
    joblib.dump(
        modelos,
        archivo_modelo_usuario(user_id)
    )


def reset_modelo_service():
    """
    Borra el modelo del usuario actual:

    - limpia memoria
    - borra modelo.pkl
    - borra info_modelo.json
    - limpia estado de entrenamiento
    """
    user_id = obtener_usuario()

    with _lock_global:
        _modelos[user_id] = None

    ruta = archivo_modelo_usuario()

    if os.path.exists(ruta):
        os.remove(ruta)

    ruta_info = archivo_info_usuario()

    if os.path.exists(ruta_info):
        os.remove(ruta_info)

    with _lock_estado:
        _estado_entrenamiento.pop(user_id, None)