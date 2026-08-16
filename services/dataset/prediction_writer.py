"""
Guardado de predicciones dentro del dataset personal del usuario.
"""

import logging

import pandas as pd

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario

from ..constants import SUFIJO_COMPOSICION

from .cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
    _firma_archivo,
)

from .loader import cargar_dataset

from .schema import (
    _columnas_composicion,
    detectar_columna_temperatura,
)

logger = logging.getLogger(__name__)


def guardar_prediccion_en_dataset(mix, temperatura, tabla_prediccion):
    """
    Guarda una predicción como fila nueva en el dataset personal
    del usuario actual.
    """
    user_id = obtener_user_id()
    df = cargar_dataset()

    columnas_composicion = _columnas_composicion(df)
    columna_temperatura = detectar_columna_temperatura(df.columns)

    fila = {col: None for col in df.columns}

    # Composición: poner en 0 todas las columnas de composición.
    for col in columnas_composicion:
        if col in fila:
            fila[col] = 0

    # Cargar los valores de la mezcla enviada.
    for e in mix:
        elemento = e.get("elemento", "")
        pct = e.get("pct")

        col = f"{elemento}{SUFIJO_COMPOSICION}"

        if col in fila:
            fila[col] = pct

    # Cargar temperatura.
    if columna_temperatura is not None and columna_temperatura in fila:
        fila[columna_temperatura] = temperatura

    # Cargar predicciones.
    for item in tabla_prediccion:
        col = item.get("columna")

        if col in fila:
            fila[col] = item.get("prediccion")

    nueva_fila = pd.DataFrame([fila])[df.columns]
    df = pd.concat([df, nueva_fila], ignore_index=True)

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
        "Predicción guardada en el dataset del usuario %s (fila %s)",
        user_id,
        len(df) - 1
    )

    return {"filas": len(df)}