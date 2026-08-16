"""
Listado seguro de filas para JSON.
"""

import numpy as np

from .schema import (
    _columnas_composicion,
    detectar_columna_temperatura,
)

from .validation import analizar_fila


def fila_a_dict_json_seguro(fila):
    """
    Convierte una fila de pandas a dict JSON-safe.
    """
    resultado = {}

    for col, val in fila.items():
        if pd.isna(val):
            resultado[col] = None
        elif isinstance(val, np.integer):
            resultado[col] = int(val)
        elif isinstance(val, np.floating):
            resultado[col] = float(val)
        else:
            resultado[col] = val

    return resultado


def listar_filas_df(df):
    """
    Devuelve columnas y filas de un DataFrame, marcando
    inconsistencias por fila.
    """
    columnas_pct = _columnas_composicion(df)
    columna_temperatura = detectar_columna_temperatura(df.columns)

    filas = []

    for i, fila in df.iterrows():
        inconsistente, motivo = analizar_fila(
            fila,
            columnas_pct,
            columna_temperatura
        )

        valores = fila_a_dict_json_seguro(fila)

        filas.append({
            "indice": int(i),
            "valores": valores,
            "inconsistente": inconsistente,
            "motivo": motivo,
        })

    return {
        "columnas": list(df.columns),
        "filas": filas,
    }


# Import acá abajo para evitar problemas de lint/orden.
import pandas as pd