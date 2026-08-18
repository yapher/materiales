"""
Estado general del sistema para el usuario actual.
Se usa desde:
- /mezclas/estado
- /admin/estado
"""
import os
import logging
from ..excel_service import cargar_dataset
from utils import archivo_modelo_usuario
from .state import (
    obtener_usuario,
    _modelos,
)
from .store import cargar_modelo
from .info import info_modelo_service

logger = logging.getLogger(__name__)


def estado_service():
    """
    Devuelve el estado general del usuario actual:
    - dataset cargado (global)
    - cantidad de filas y columnas
    - modelo en memoria
    - modelo persistido
    - información del último entrenamiento
    """
    user_id = obtener_usuario()

    if _modelos[user_id] is None:
        cargar_modelo()

    try:
        df = cargar_dataset()
        dataset_ok = True
        filas = len(df)
        columnas = len(df.columns)
    except Exception as e:
        logger.error(
            "Error cargando dataset global: %s", e
        )
        dataset_ok = False
        filas = 0
        columnas = 0

    return {
        "usuario": user_id,
        "dataset_cargado": dataset_ok,
        "filas_dataset": filas,
        "columnas_dataset": columnas,
        "modelo_en_memoria": _modelos[user_id] is not None,
        "modelo_persistido": os.path.exists(archivo_modelo_usuario()),
        "modelo_info": info_modelo_service(),
    }