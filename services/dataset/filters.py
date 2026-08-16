"""
Filtrado de filas para entrenamiento.

Reglas:

1. Se EXCLUYEN filas donde la composición no suma 100%
   (± tolerancia) o faltan porcentajes de composición.

2. Si la temperatura tiene un valor inconsistente (vacío,
   no numérico, lo que fuere), NO se descarta la fila:
   se reemplaza la temperatura por 0.
"""

import logging

import pandas as pd

from .schema import (
    _columnas_composicion,
    detectar_columna_temperatura,
    obtener_feature_columns,
)

logger = logging.getLogger(__name__)

TOLERANCIA_SUMA_PCT_ENTRENAMIENTO = 0.5


def obtener_filas_entrenables(df):
    """
    Devuelve una máscara booleana indicando qué filas son aptas
    para entrenar.

    Criterio de exclusión: SOLO la composición.

    - Todas las columnas *_pct de composición deben tener valor.
    - La suma de *_pct debe dar 100 ± tolerancia.

    La temperatura NO excluye: si falta o es inválida,
    se rellena con 0 en filtrar_dataset_entrenamiento().
    """
    columnas_pct = _columnas_composicion(df)

    if not columnas_pct:
        features = obtener_feature_columns(df)

        if not features:
            return pd.Series(True, index=df.index)

        columna_temperatura = detectar_columna_temperatura(df.columns)

        features_sin_temp = [
            f for f in features
            if f != columna_temperatura
        ]

        if not features_sin_temp:
            return pd.Series(True, index=df.index)

        feat_df = df[features_sin_temp].apply(pd.to_numeric, errors="coerce")
        return feat_df.notna().all(axis=1)

    comp_df = df[columnas_pct].apply(pd.to_numeric, errors="coerce")
    comp_completa = comp_df.notna().all(axis=1)

    suma_pct = comp_df.sum(axis=1)

    suma_ok = (
        (suma_pct >= 100 - TOLERANCIA_SUMA_PCT_ENTRENAMIENTO)
        & (suma_pct <= 100 + TOLERANCIA_SUMA_PCT_ENTRENAMIENTO)
    )

    mascara = comp_completa & suma_ok

    return mascara


def filtrar_dataset_entrenamiento(df):
    """
    Devuelve una copia del DataFrame solo con las filas aptas
    para entrenamiento, con la temperatura inconsistente
    reemplazada por 0.

    Se EXCLUYEN filas donde:

    - falta algún porcentaje de composición,
    - la suma de óxidos/composición no da 100 ± tolerancia.

    NO se excluyen filas por temperatura:

    - Si la temperatura falta, está vacía, o no es numérica,
      se reemplaza por 0.

    Devuelve: (df_filtrado, info)
    """
    mascara = obtener_filas_entrenables(df)
    df_limpio = df[mascara].copy()

    columna_temperatura = detectar_columna_temperatura(df_limpio.columns)
    temperatura_reemplazada = 0

    if (
        columna_temperatura is not None
        and columna_temperatura in df_limpio.columns
    ):
        temp_original = df_limpio[columna_temperatura]
        temp_numerica = pd.to_numeric(temp_original, errors="coerce")

        temperatura_reemplazada = int(temp_numerica.isna().sum())
        df_limpio[columna_temperatura] = temp_numerica.fillna(0)

        logger.info(
            "Temperatura: %s filas con valor inconsistente "
            "reemplazadas por 0.",
            temperatura_reemplazada,
        )

    total = len(df)
    retenidas = len(df_limpio)
    excluidas = total - retenidas

    columnas_pct = _columnas_composicion(df)

    reglas = []

    if columnas_pct:
        reglas.append(
            f"composición completa y suma 100% "
            f"± {TOLERANCIA_SUMA_PCT_ENTRENAMIENTO}"
        )

    if columna_temperatura is not None:
        reglas.append(
            "temperatura inconsistente reemplazada por 0"
        )

    return df_limpio, {
        "filas_totales": total,
        "filas_entrenables": retenidas,
        "filas_excluidas": excluidas,
        "temperatura_reemplazada_por_0": temperatura_reemplazada,
        "reglas": reglas,
    }