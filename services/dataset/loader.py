"""
Carga y recarga de datasets personales de usuario.
"""

import logging

import pandas as pd

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario

from .cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
    _firma_archivo,
)

from .files import inicializar_dataset_usuario

logger = logging.getLogger(__name__)


def cargar_dataset(user_id=None):
    """
    Carga el dataset personal del usuario actual.

    Usa cache en memoria. Si el archivo cambió en disco,
    lo vuelve a leer.
    """
    user_id = user_id or obtener_user_id()

    with _lock_dataset:
        archivo = archivo_dataset_usuario(user_id)
        firma_actual = _firma_archivo(archivo)

        if (
            user_id in _datasets
            and firma_actual is not None
            and _dataset_firmas.get(user_id) == firma_actual
        ):
            return _datasets[user_id]

        archivo = inicializar_dataset_usuario(user_id)
        firma_actual = _firma_archivo(archivo)

        if (
            user_id in _datasets
            and firma_actual is not None
            and _dataset_firmas.get(user_id) == firma_actual
        ):
            return _datasets[user_id]

        logger.info("Leyendo dataset usuario %s", user_id)

        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all")

        _datasets[user_id] = df
        _dataset_firmas[user_id] = firma_actual

        logger.info(
            "Dataset usuario %s cargado (%s filas)",
            user_id,
            len(df)
        )

        return _datasets[user_id]


def recargar_dataset(user_id=None):
    """
    Fuerza la recarga del dataset personal del usuario.
    """
    user_id = user_id or obtener_user_id()

    with _lock_dataset:
        archivo = inicializar_dataset_usuario(user_id)

        logger.info(
            "Recargando dataset usuario %s desde %s",
            user_id,
            archivo
        )

        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all")

        _datasets[user_id] = df
        _dataset_firmas[user_id] = _firma_archivo(archivo)

        logger.info("Dataset usuario %s actualizado", user_id)

        return df


def forzar_recarga_usuario(user_id=None):
    """
    Alias usado por admin y subida de dataset maestro.
    """
    return recargar_dataset(user_id)


def dataset_cargado():
    """
    Indica si el dataset del usuario actual ya está en memoria.
    """
    user_id = obtener_user_id()
    return user_id in _datasets


def cargar_excel_service():
    """
    Devuelve información básica del dataset actual.
    """
    df = cargar_dataset()

    return {
        "filas": len(df),
        "columnas": len(df.columns),
    }