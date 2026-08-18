"""
Carga y recarga del dataset global (maestro).
Ya NO existen datasets personales por usuario.
Todos los usuarios trabajan sobre el mismo dataset maestro.
"""
import logging
import pandas as pd
from config import Config
from .cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
    _firma_archivo,
)

logger = logging.getLogger(__name__)

# Clave única para el dataset global
_GLOBAL_KEY = "__global__"


def cargar_dataset(user_id=None):
    """
    Carga el dataset maestro (global).
    El parámetro user_id se mantiene por compatibilidad pero se ignora:
    todos los usuarios ven el mismo dataset.
    """
    with _lock_dataset:
        archivo = Config.ARCHIVO_DATASET
        firma_actual = _firma_archivo(archivo)

        if (
            _GLOBAL_KEY in _datasets
            and firma_actual is not None
            and _dataset_firmas.get(_GLOBAL_KEY) == firma_actual
        ):
            return _datasets[_GLOBAL_KEY]

        logger.info("Leyendo dataset maestro (global): %s", archivo)
        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all")

        _datasets[_GLOBAL_KEY] = df
        _dataset_firmas[_GLOBAL_KEY] = firma_actual

        logger.info(
            "Dataset global cargado (%s filas)",
            len(df)
        )
        return _datasets[_GLOBAL_KEY]


def recargar_dataset(user_id=None):
    """
    Fuerza la recarga del dataset maestro desde disco.
    """
    with _lock_dataset:
        archivo = Config.ARCHIVO_DATASET
        logger.info(
            "Recargando dataset maestro desde %s",
            archivo
        )
        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all")

        _datasets[_GLOBAL_KEY] = df
        _dataset_firmas[_GLOBAL_KEY] = _firma_archivo(archivo)

        logger.info("Dataset global actualizado")
        return df


def forzar_recarga_usuario(user_id=None):
    """
    Alias de compatibilidad. Ahora recarga el dataset global.
    """
    return recargar_dataset(user_id)


def dataset_cargado():
    """
    Indica si el dataset global ya está en memoria.
    """
    return _GLOBAL_KEY in _datasets


def cargar_excel_service():
    """
    Devuelve información básica del dataset actual.
    """
    df = cargar_dataset()
    return {
        "filas": len(df),
        "columnas": len(df.columns),
    }