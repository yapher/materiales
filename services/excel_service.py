import logging
import threading
import os
import shutil

import pandas as pd
import numpy as np

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario

logger = logging.getLogger(__name__)

# ==========================================================
# Compatibilidad con services/constants.py dinámico.
# ==========================================================
try:
    from .constants import (
        SUFIJO_COMPOSICION,
        PREFERENCIA_TEMPERATURA,
        CANTIDAD_COLUMNAS_COMPOSICION,
        es_columna_temperatura,
        etiqueta_amigable,
        descripcion_variable,
        etiqueta_temperatura,
        normalizar_nombre_columna,
    )
except ImportError:
    import re

    SUFIJO_COMPOSICION = "_pct"

    PREFERENCIA_TEMPERATURA = [
        "Temperatura_K",
        "Temperatura_k",
        "Temperatura_C",
        "Temperatura",
        "Temperature_K",
        "Temperature_C",
        "Temperature",
        "Temp_K",
        "Temp_C",
        "Temp",
    ]

    CANTIDAD_COLUMNAS_COMPOSICION = int(
        os.environ.get("CANTIDAD_COLUMNAS_COMPOSICION", "11")
    )

    _PATRON_TEMPERATURA = re.compile(r"^temp(eratura|erature)?(_(k|c))?$")

    def normalizar_nombre_columna(columna):
        return str(columna).strip().lower().replace(" ", "_")

    def es_columna_temperatura(columna):
        norm = normalizar_nombre_columna(columna)
        return bool(_PATRON_TEMPERATURA.match(norm))

    def etiqueta_amigable(columna):
        return str(columna).replace("_", " ").strip()

    def descripcion_variable(columna):
        return f"Variable '{columna}' detectada automáticamente del dataset."

    def etiqueta_temperatura(columna):
        if not columna:
            return "Temperatura"

        norm = normalizar_nombre_columna(columna)

        if norm.endswith("_k"):
            return "Temperatura (K)"

        if norm.endswith("_c"):
            return "Temperatura (°C)"

        return etiqueta_amigable(columna)


# ==========================================================
# CACHE DATASET POR USUARIO (en memoria del proceso)
# ==========================================================
_datasets = {}
_dataset_firmas = {}
_lock_dataset = threading.Lock()


def _firma_archivo(ruta):
    try:
        st = os.stat(ruta)
        mtime = getattr(st, "st_mtime_ns", None)
        if mtime is None:
            mtime = int(st.st_mtime * 1_000_000_000)
        return (mtime, st.st_size)
    except OSError:
        return None


# ==========================================================
# CREAR DATASET DEL USUARIO (copia la plantilla si no existe)
# ==========================================================
def inicializar_dataset_usuario(user_id=None):
    user_id = user_id or obtener_user_id()
    archivo = archivo_dataset_usuario(user_id)

    if not os.path.exists(archivo):
        logger.info("Creando dataset para usuario %s", user_id)
        shutil.copy(
            Config.ARCHIVO_DATASET,
            archivo
        )

    return archivo


# ==========================================================
# CARGAR DATASET (con cache en memoria por usuario)
# ==========================================================
def cargar_dataset(user_id=None):
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


# ==========================================================
# RECARGAR DATASET
# ==========================================================
def recargar_dataset(user_id=None):
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
    return recargar_dataset(user_id)


# ==========================================================
# ESTADO: dataset del usuario actual ya está en memoria?
# ==========================================================
def dataset_cargado():
    user_id = obtener_user_id()
    return user_id in _datasets


# ==========================================================
# INFO RESUMIDA DEL DATASET
# ==========================================================
def cargar_excel_service():
    df = cargar_dataset()
    return {
        "filas": len(df),
        "columnas": len(df.columns),
    }


# ==========================================================
# DETECCIÓN DINÁMICA DE COLUMNAS
# ==========================================================
def _es_columna_numerica(df, columna):
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

    IMPORTANTE:
    El dataset actual tiene esta estructura:
    - Columnas A a K: elementos de composición.
    - Columna L en adelante: variables a modelar.

    Por eso NO alcanza con buscar todas las columnas terminadas
    en '_pct', porque puede haber variables objetivo que también
    terminen en '_pct', por ejemplo:
    - C_libre_pct
    - Fraccion_Cristalina_pct

    Esas columnas NO son elementos de la mezcla: son variables
    entrenables y están de la columna L hacia adelante.

    Regla aplicada:
    - Solo se consideran composición las columnas terminadas en
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
    Se usa también desde dataset_upload_service para validar
    archivos subidos por el administrador.
    """
    return _columnas_composicion(df)


def detectar_columna_temperatura(columnas):
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

    Regla:
    - Las columnas de composición son las primeras 11 columnas
      del dataset (A-K) que terminan en '_pct'.
    - La columna de temperatura, si existe, es feature.
    - Las variables entrenables se buscan desde la columna L
      en adelante, es decir, desde el índice 11.

    Esto evita que variables objetivo que estén en columnas
    posteriores, pero que terminen en '_pct', sean tratadas
    como elementos de composición.
    """
    features = obtener_feature_columns(df)
    feature_set = set(features)
    limite = int(CANTIDAD_COLUMNAS_COMPOSICION)

    targets = []

    for indice, col in enumerate(df.columns):
        if col in feature_set:
            continue

        # No convertir en target ninguna columna del bloque inicial
        # de composición (A-K), salvo que ya sea feature por temperatura.
        if indice < limite:
            continue

        if _es_columna_numerica(df, col):
            targets.append(col)

    return targets


def obtener_esquema_dataset(user_id=None):
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


# ==========================================================
# FILTRADO DE FILAS INCONSISTENTES PARA ENTRENAMIENTO
#
# REGLAS:
# 1. Se EXCLUYEN filas donde la composición no suma 100%
#    (± tolerancia) o faltan porcentajes de composición.
# 2. Si la temperatura tiene un valor inconsistente (vacío,
#    no numérico, lo que fuere), NO se descarta la fila:
#    se reemplaza la temperatura por 0.
# ==========================================================
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


# ==========================================================
# GUARDAR UNA PREDICCION COMO FILA NUEVA EN EL DATASET PERSONAL
# ==========================================================
def guardar_prediccion_en_dataset(mix, temperatura, tabla_prediccion):
    user_id = obtener_user_id()
    df = cargar_dataset()

    columnas_composicion = _columnas_composicion(df)
    columna_temperatura = detectar_columna_temperatura(df.columns)

    fila = {col: None for col in df.columns}

    for col in columnas_composicion:
        if col in fila:
            fila[col] = 0

    for e in mix:
        elemento = e.get("elemento", "")
        pct = e.get("pct")
        col = f"{elemento}{SUFIJO_COMPOSICION}"

        if col in fila:
            fila[col] = pct

    if columna_temperatura is not None and columna_temperatura in fila:
        fila[columna_temperatura] = temperatura

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


# ==========================================================
# DATASET MAESTRO (administración, solo para el admin)
# ==========================================================
_dataset_maestro = None
_dataset_maestro_firma = None
_lock_maestro = threading.Lock()

TOLERANCIA_SUMA_PCT = 0.5


def _analizar_fila(fila, columnas_pct, columna_temperatura=None):
    motivos = []

    columnas_obligatorias = list(columnas_pct)

    if columna_temperatura is not None and columna_temperatura in fila.index:
        columnas_obligatorias.append(columna_temperatura)

    faltantes = [
        c for c in columnas_obligatorias
        if pd.isna(fila.get(c))
    ]

    if faltantes:
        motivos.append(f"Faltan valores en: {', '.join(faltantes)}")

    presentes = [
        c for c in columnas_pct
        if not pd.isna(fila.get(c))
    ]

    if presentes:
        suma = sum(fila.get(c, 0) for c in presentes)

        if abs(suma - 100) > TOLERANCIA_SUMA_PCT:
            motivos.append(
                f"La composición suma {round(suma, 2)}%, no 100%"
            )

    if motivos:
        return True, "; ".join(motivos)

    return False, None


def cargar_dataset_maestro(forzar=False):
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


def _fila_a_dict_json_seguro(fila):
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


def _listar_filas_df(df):
    columnas_pct = _columnas_composicion(df)
    columna_temperatura = detectar_columna_temperatura(df.columns)

    filas = []

    for i, fila in df.iterrows():
        inconsistente, motivo = _analizar_fila(
            fila,
            columnas_pct,
            columna_temperatura
        )

        valores = _fila_a_dict_json_seguro(fila)

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


def listar_filas_maestro():
    df = cargar_dataset_maestro()
    return _listar_filas_df(df)


def obtener_fila_maestro(indice):
    data = listar_filas_maestro()

    fila = next(
        (f for f in data["filas"] if f["indice"] == indice),
        None
    )

    if fila is None:
        raise ValueError("Fila inexistente")

    return data["columnas"], fila


def listar_filas_usuario():
    df = cargar_dataset()
    return _listar_filas_df(df)


def obtener_fila_usuario(indice):
    data = listar_filas_usuario()

    fila = next(
        (f for f in data["filas"] if f["indice"] == indice),
        None
    )

    if fila is None:
        raise ValueError("Fila inexistente")

    return data["columnas"], fila


def actualizar_fila_usuario(indice, valores):
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


def actualizar_fila_maestro(indice, valores):
    df = cargar_dataset_maestro()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    for col, val in valores.items():
        if col in df.columns:
            df.at[indice, col] = val

    guardar_dataset_maestro(df)

    return df


def eliminar_fila_maestro(indice):
    df = cargar_dataset_maestro()

    if indice < 0 or indice >= len(df):
        raise ValueError("Fila inexistente")

    df = df.drop(index=indice).reset_index(drop=True)
    guardar_dataset_maestro(df)

    return df


def agregar_fila_maestro(valores):
    df = cargar_dataset_maestro()

    nueva = {col: valores.get(col) for col in df.columns}

    df = pd.concat(
        [df, pd.DataFrame([nueva])],
        ignore_index=True
    )

    guardar_dataset_maestro(df)

    return df