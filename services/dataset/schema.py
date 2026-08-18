"""
Detección dinámica de columnas del dataset.
Reglas actuales:
- Columnas A a K: composición.
- Columna L en adelante: variables entrenables.
- La columna de temperatura es feature.
"""
import pandas as pd
from ..constants import (
    SUFIJO_COMPOSICION,
    PREFERENCIA_TEMPERATURA,
    CANTIDAD_COLUMNAS_COMPOSICION,
    es_columna_temperatura,
    etiqueta_amigable,
    descripcion_variable,
    etiqueta_temperatura,
    normalizar_nombre_columna,
)
from .loader import cargar_dataset


def _es_columna_numerica(df, columna):
    """
    Devuelve True si la columna tiene valores numéricos útiles.
    """
    if columna not in df.columns:
        return False
    if pd.api.types.is_numeric_dtype(df[columna]):
        return True
    try:
        serie = pd.to_numeric(df[columna], errors="coerce")
        return bool(serie.notna().any())
    except Exception:
        return False


def _columnas_composicion(df):
    """
    Devuelve las columnas de composición.
    Solo se consideran composición las columnas terminadas en
    '_pct' que estén dentro de las primeras
    CANTIDAD_COLUMNAS_COMPOSICION columnas del Excel.
    """
    columnas = []
    limite = int(CANTIDAD_COLUMNAS_COMPOSICION)
    for indice, col in enumerate(df.columns):
        if indice >= limite:
            break
        if str(col).lower().endswith(SUFIJO_COMPOSICION):
            columnas.append(col)
    return columnas


def obtener_columnas_composicion(df):
    """
    Wrapper público de _columnas_composicion().
    """
    return _columnas_composicion(df)


def detectar_columna_temperatura(columnas):
    """
    Detecta la columna de temperatura del dataset.
    """
    mapa_normalizado = {
        normalizar_nombre_columna(c): c
        for c in columnas
    }
    for nombre in PREFERENCIA_TEMPERATURA:
        clave = normalizar_nombre_columna(nombre)
        if clave in mapa_normalizado:
            return mapa_normalizado[clave]
    for col in columnas:
        if es_columna_temperatura(col):
            return col
    return None


def obtener_feature_columns(df):
    """
    Devuelve las features:
    - columnas de composición A-K terminadas en _pct
    - columna de temperatura, si existe
    """
    composicion = _columnas_composicion(df)
    temperatura = detectar_columna_temperatura(df.columns)
    features = list(composicion)
    if temperatura is not None and temperatura in df.columns:
        if temperatura not in features:
            features.append(temperatura)
    return features


def obtener_target_columns(df):
    """
    Devuelve las variables a modelar (targets).
    """
    features = obtener_feature_columns(df)
    feature_set = set(features)
    limite = int(CANTIDAD_COLUMNAS_COMPOSICION)
    targets = []
    for indice, col in enumerate(df.columns):
        if col in feature_set:
            continue
        if indice < limite:
            continue
        if _es_columna_numerica(df, col):
            targets.append(col)
    return targets


def obtener_esquema_dataset(user_id=None):
    """
    Devuelve el esquema dinámico del dataset global.
    El parámetro user_id se mantiene por compatibilidad pero se ignora.
    """
    df = cargar_dataset(user_id)

    columnas_composicion = _columnas_composicion(df)
    elementos = [
        str(col)[: -len(SUFIJO_COMPOSICION)]
        for col in columnas_composicion
    ]

    columna_temperatura = detectar_columna_temperatura(df.columns)
    targets = obtener_target_columns(df)

    default_target = None
    if targets:
        preferidas = [
            "Densidad_kg_m3",
            "densidad_kg_m3",
            "Densidad",
            "densidad",
        ]
        for candidata in preferidas:
            clave_candidata = normalizar_nombre_columna(candidata)
            match = next(
                (
                    t for t in targets
                    if normalizar_nombre_columna(t) == clave_candidata
                ),
                None
            )
            if match:
                default_target = match
                break
        if default_target is None:
            default_target = targets[0]

    variables_entrenables = []
    for target in targets:
        variables_entrenables.append({
            "valor": target,
            "etiqueta": etiqueta_amigable(target),
            "descripcion": descripcion_variable(target),
            "por_defecto": target == default_target,
        })

    return {
        "elementos": elementos,
        "columnas_composicion": columnas_composicion,
        "temperatura_column": columna_temperatura,
        "temperatura_etiqueta": etiqueta_temperatura(columna_temperatura),
        "variables_entrenables": variables_entrenables,
        "variable_entrenable_default": default_target,
        "features": obtener_feature_columns(df),
    }