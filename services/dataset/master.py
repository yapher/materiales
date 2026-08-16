"""
Dataset maestro.

Es la plantilla global que se copia a cada usuario nuevo.
Solo el admin lo edita directamente.
"""

import logging
import threading

import pandas as pd

from config import Config

from .cache import _firma_archivo
from .listing import listar_filas_df

logger = logging.getLogger(__name__)

_dataset_maestro = None
_dataset_maestro_firma = None
_lock_maestro = threading.Lock()


def cargar_dataset_maestro(forzar=False):
    """
    Carga el dataset maestro en memoria.
    """
    global _dataset_maestro
    global _dataset_maestro_firma

    with _lock_maestro:
        archivo = Config.ARCHIVO_DATASET
        firma_actual = _firma_archivo(archivo)

        if (
            not forzar
            and _dataset_maestro is not None
            and _dataset_maestro_firma == firma_actual
        ):
            return _dataset_maestro

        logger.info(
            "Leyendo dataset maestro (%s)",
            archivo
        )

        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all").reset_index(drop=True)

        _dataset_maestro = df
        _dataset_maestro_firma = firma_actual

        return _dataset_maestro


def guardar_dataset_maestro(df):
    """
    Guarda el dataset maestro en disco y actualiza la cache.
    """
    global _dataset_maestro
    global _dataset_maestro_firma

    with _lock_maestro:
        df.to_excel(
            Config.ARCHIVO_DATASET,
            sheet_name=Config.HOJA_DATASET,
            index=False
        )

        _dataset_maestro = df
        _dataset_maestro_firma = _firma_archivo(Config.ARCHIVO_DATASET)

        logger.info("Dataset maestro guardado (%s filas)", len(df))


def listar_filas_maestro():
    """
    Lista las filas del dataset maestro.
    """
    df = cargar_dataset_maestro()
    return listar_filas_df(df)


def obtener_fila_maestro(indice):
    """
    Devuelve columnas y una fila del dataset maestro.
    """
    data = listar_filas_maestro()

    fila = next(
        (f for f in data["filas"] if f["indice"] == indice),
        None
    )

    if fila is None:
        raise ValueError("Fila inexistente")

    return data["columnas"], fila


def actualizar_fila_maestro(indice, valores):
    """
    Actualiza una fila del dataset maestro.
    """
    df = cargar_dataset_maestro()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    for col, val in valores.items():
        if col in df.columns:
            df.at[indice, col] = val

    guardar_dataset_maestro(df)

    return df


def eliminar_fila_maestro(indice):
    """
    Elimina una fila del dataset maestro.
    """
    df = cargar_dataset_maestro()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    df = df.drop(index=indice).reset_index(drop=True)
    guardar_dataset_maestro(df)

    return df


def agregar_fila_maestro(valores):
    """
    Agrega una fila nueva al dataset maestro.
    """
    df = cargar_dataset_maestro()

    nueva = {col: valores.get(col) for col in df.columns}

    df = pd.concat(
        [df, pd.DataFrame([nueva])],
        ignore_index=True
    )

    guardar_dataset_maestro(df)

    return df