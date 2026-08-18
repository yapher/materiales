"""
Guardado de predicciones dentro del dataset global.
SOLO el administrador puede guardar predicciones en el dataset.
Al guardar, se invalida el modelo entrenado.
"""
import logging
import pandas as pd
from config import Config
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
    Guarda una predicción como fila nueva en el dataset global.
    SOLO debe ser invocado por el administrador.
    Después de guardar, el modelo debe ser borrado (lo hace la ruta).
    """
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

    # Guardar en el archivo maestro
    df.to_excel(
        Config.ARCHIVO_DATASET,
        sheet_name=Config.HOJA_DATASET,
        index=False
    )

    # Invalidar cache
    _GLOBAL_KEY = "__global__"
    with _lock_dataset:
        _datasets[_GLOBAL_KEY] = df
        _dataset_firmas[_GLOBAL_KEY] = _firma_archivo(
            Config.ARCHIVO_DATASET
        )

    logger.info(
        "Predicción guardada en el dataset global (fila %s)",
        len(df) - 1
    )
    return {"filas": len(df)}