"""
Extracción de puntos reales del dataset para el gráfico
densidad vs. temperatura.

Solo se incluyen filas que tienen EXACTAMENTE la misma
composición que la mezcla actual (dentro de una tolerancia),
con la información completa de cada fila.
"""

import logging

import numpy as np
import pandas as pd

from ...dataset import (
    cargar_dataset,
    detectar_columna_temperatura,
    obtener_columnas_composicion,
)

logger = logging.getLogger(__name__)

# Cantidad máxima de puntos reales que se grafican.
MAX_PUNTOS_REALES = 500

# Tolerancia para comparar composiciones (±0.5 puntos porcentuales).
TOLERANCIA_COMPOSICION = 0.5


def _fila_a_dict_seguro(fila, columnas):
    """
    Convierte una fila de pandas a un dict JSON-safe.
    Maneja NaN, tipos numpy y valores no serializables.
    """
    resultado = {}
    for col in columnas:
        try:
            val = fila[col]
        except (KeyError, IndexError):
            resultado[col] = None
            continue

        if pd.isna(val):
            resultado[col] = None
        elif isinstance(val, (np.integer,)):
            resultado[col] = int(val)
        elif isinstance(val, (np.floating,)):
            resultado[col] = round(float(val), 4)
        elif isinstance(val, (int, float)):
            resultado[col] = (
                round(float(val), 4)
                if isinstance(val, float)
                else val
            )
        else:
            resultado[col] = str(val)
    return resultado


def _extraer_puntos_reales(df, columna_densidad, composicion_esperada):
    """
    Extrae del DataFrame del dataset los puntos (temperatura, densidad)
    de las filas que tienen EXACTAMENTE la misma composición que la
    mezcla actual.

    composicion_esperada es un dict:
        {"CaO_pct": 25.0, "SiO2_pct": 40.0, "MnO_pct": 35.0, ...}

    Solo se incluyen filas donde TODAS las columnas de composición
    coinciden con los valores esperados (dentro de la tolerancia).
    Cada punto incluye la información completa de la fila del dataset.

    Devuelve una lista de dicts con 'temperatura', 'densidad' y 'fila',
    ordenada por temperatura.
    """
    if df is None or df.empty:
        return []
    if columna_densidad not in df.columns:
        return []

    columna_temperatura = detectar_columna_temperatura(df.columns)
    if (
        columna_temperatura is None
        or columna_temperatura not in df.columns
    ):
        return []

    temp_serie = pd.to_numeric(
        df[columna_temperatura],
        errors="coerce",
    )
    dens_serie = pd.to_numeric(
        df[columna_densidad],
        errors="coerce",
    )

    # Máscara de coincidencia exacta de composición
    mascara_composicion = pd.Series(True, index=df.index)
    for col_pct, valor_esperado in composicion_esperada.items():
        if col_pct in df.columns:
            col_serie = pd.to_numeric(
                df[col_pct],
                errors="coerce",
            ).fillna(0)
            mascara_composicion &= (
                (col_serie - valor_esperado).abs()
                <= TOLERANCIA_COMPOSICION
            )

    # Máscara combinada: datos válidos + composición exacta.
    mascara_valida = (
        temp_serie.notna()
        & dens_serie.notna()
        & (dens_serie > 0)
        & mascara_composicion
    )

    # Columnas del dataset para incluir en la info de fila
    columnas_dataset = list(df.columns)

    puntos = []
    indices_validos = df.index[mascara_valida]
    for indice in indices_validos:
        fila_info = _fila_a_dict_seguro(
            df.loc[indice],
            columnas_dataset,
        )
        puntos.append({
            "temperatura": round(float(temp_serie.at[indice]), 4),
            "densidad": round(float(dens_serie.at[indice]), 4),
            "fila": fila_info,
            "indice_dataset": int(indice),
        })

    # Ordenar por temperatura
    puntos.sort(key=lambda p: p["temperatura"])

    # Limitar la cantidad de puntos
    if len(puntos) > MAX_PUNTOS_REALES:
        paso = len(puntos) // MAX_PUNTOS_REALES + 1
        puntos = puntos[::paso]

    return puntos


def _obtener_puntos_reales_dataset(user_id, columna_densidad, mix):
    """
    Carga el dataset del usuario y extrae los puntos reales de
    densidad vs. temperatura que tienen EXACTAMENTE la misma
    composición que la mezcla actual.

    Cada punto incluye la información completa de la fila del dataset.
    Devuelve una lista de dicts {'temperatura', 'densidad', 'fila'}.
    Nunca lanza: ante cualquier problema devuelve una lista vacía.
    """
    try:
        df = cargar_dataset(user_id)
    except Exception:
        logger.warning(
            "No se pudo cargar el dataset del usuario %s para "
            "obtener puntos reales.",
            user_id,
        )
        return []

    try:
        columnas_composicion = obtener_columnas_composicion(df)
    except Exception:
        logger.warning(
            "No se pudieron detectar columnas de composición "
            "para el usuario %s.",
            user_id,
        )
        return []

    # Construir la composición esperada
    composicion_esperada = {
        col: 0.0 for col in columnas_composicion
    }
    if isinstance(mix, list):
        for elemento in mix:
            if not isinstance(elemento, dict):
                continue
            nombre = elemento.get("elemento", "")
            pct = elemento.get("pct", 0)
            col = f"{nombre}_pct"
            if col in composicion_esperada:
                try:
                    composicion_esperada[col] = float(pct)
                except (TypeError, ValueError):
                    composicion_esperada[col] = 0.0

    try:
        puntos = _extraer_puntos_reales(
            df,
            columna_densidad,
            composicion_esperada,
        )
    except Exception:
        logger.exception(
            "Error extrayendo puntos reales del dataset (usuario %s)",
            user_id,
        )
        return []

    logger.info(
        "Puntos reales del dataset para usuario %s con la misma "
        "composición: %s puntos encontrados.",
        user_id,
        len(puntos),
    )
    return puntos