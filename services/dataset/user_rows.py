"""
Operaciones sobre filas del dataset personal del usuario.
"""

import logging

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario

from .cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
    _firma_archivo,
)

from .loader import cargar_dataset
from .listing import listar_filas_df

logger = logging.getLogger(__name__)


def listar_filas_usuario():
    """
    Lista las filas del dataset personal del usuario actual.
    """
    df = cargar_dataset()
    return listar_filas_df(df)


def obtener_fila_usuario(indice):
    """
    Devuelve columnas y una fila del dataset personal.
    """
    data = listar_filas_usuario()

    fila = next(
        (f for f in data["filas"] if f["indice"] == indice),
        None
    )

    if fila is None:
        raise ValueError("Fila inexistente")

    return data["columnas"], fila


def actualizar_fila_usuario(indice, valores):
    """
    Actualiza una fila del dataset personal del usuario actual.
    """
    user_id = obtener_user_id()
    df = cargar_dataset()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    for col, val in valores.items():
        if col in df.columns:
            df.at[indice, col] = val

    archivo = archivo_dataset_usuario()

    df.to_excel(
        archivo,
        sheet_name=Config.HOJA_DATASET,
        index=False
    )

    with _lock_dataset:
        _datasets[user_id] = df
        _dataset_firmas[user_id] = _firma_archivo(archivo)

    logger.info(
        "Fila %s actualizada en el dataset del usuario %s",
        indice,
        user_id
    )

    return df


def eliminar_fila_usuario(indice):
    """
    Elimina una fila del dataset personal del usuario actual.
    """
    user_id = obtener_user_id()
    df = cargar_dataset()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    df = df.drop(index=indice).reset_index(drop=True)

    archivo = archivo_dataset_usuario()

    df.to_excel(
        archivo,
        sheet_name=Config.HOJA_DATASET,
        index=False
    )

    with _lock_dataset:
        _datasets[user_id] = df
        _dataset_firmas[user_id] = _firma_archivo(archivo)

    logger.info(
        "Fila %s eliminada del dataset del usuario %s",
        indice,
        user_id
    )

    return df