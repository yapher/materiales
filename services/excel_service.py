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
#
# Si ya aplicaste la versión dinámica de constants.py, usa esos helpers.
# Si no, deja funcionando una versión mínima local.
# ==========================================================
try:
    from .constants import (
        SUFIJO_COMPOSICION,
        PREFERENCIA_TEMPERATURA,
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
#
# Además del DataFrame, guardamos una "firma" del archivo
# (tamaño + fecha de modificación). Si el archivo cambia en disco,
# por ejemplo cuando Admin sube un dataset nuevo, el sistema lo
# detecta y vuelve a leerlo.
# ==========================================================
_datasets = {}
_dataset_firmas = {}
_lock_dataset = threading.Lock()


def _firma_archivo(ruta):
    """
    Devuelve una firma simple del archivo para detectar cambios:
    (fecha de modificación, tamaño).

    Si el archivo no existe o no se puede leer, devuelve None.
    """
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
#
# IMPORTANTE:
# Si el archivo personal del usuario cambió en disco, se vuelve
# a cargar automáticamente. Esto evita quedarnos con el dataset
# viejo después de subir un nuevo dataset desde Admin.
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
    """
    Fuerza la lectura del dataset personal del usuario desde disco
    y actualiza la cache en memoria.
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
    Alias claro para usar desde Admin cuando se sube un nuevo dataset.
    """
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
    """
    Devuelve True si la columna es numérica o puede convertirse
    a numérica.
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
    Detecta las columnas de composición.
    Por convención terminan en _pct.
    """
    columnas = []

    for col in df.columns:
        if str(col).lower().endswith(SUFIJO_COMPOSICION):
            columnas.append(col)

    return columnas


def detectar_columna_temperatura(columnas):
    """
    Detecta la columna de temperatura del dataset.

    Prioridad:
    1. Nombres exactos conocidos.
    2. Números simples tipo Temperatura_K, Temperatura_C, Temp, etc.
    """
    mapa_normalizado = {
        normalizar_nombre_columna(c): c
        for c in columnas
    }

    # 1) Buscar nombres exactos preferidos
    for nombre in PREFERENCIA_TEMPERATURA:
        clave = normalizar_nombre_columna(nombre)

        if clave in mapa_normalizado:
            return mapa_normalizado[clave]

    # 2) Buscar patrón simple de temperatura
    for col in columnas:
        if es_columna_temperatura(col):
            return col

    return None


def obtener_feature_columns(df):
    """
    Devuelve las columnas de entrada del modelo:
    - todas las *_pct
    - la columna de temperatura, si existe
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
    Devuelve las variables a modelar.

    Criterio:
    - Se toma como zona de variables entrenables las columnas que
      aparecen luego de las columnas de entrada (features).
    - Si no detectara ninguna ahí, busca cualquier numérica que no
      sea feature.
    """
    features = obtener_feature_columns(df)
    feature_set = set(features)

    columnas = list(df.columns)

    indices_features = [
        columnas.index(col)
        for col in feature_set
        if col in columnas
    ]

    if indices_features:
        inicio_targets = max(indices_features) + 1
    else:
        inicio_targets = 0

    targets = []

    # 1) Buscar desde después de las features
    for col in columnas[inicio_targets:]:
        if col in feature_set:
            continue

        if _es_columna_numerica(df, col):
            targets.append(col)

    # 2) Fallback: cualquier numérica no feature
    if not targets:
        for col in columnas:
            if col in feature_set:
                continue

            if _es_columna_numerica(df, col):
                targets.append(col)

    return targets


def obtener_esquema_dataset(user_id=None):
    """
    Devuelve el esquema dinámico del dataset actual:

    - elementos de composición
    - columna de temperatura
    - label de temperatura
    - variables entrenables
    - variable entrenable por defecto
    - features
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


# ==========================================================
# GUARDAR UNA PREDICCION COMO FILA NUEVA EN EL DATASET PERSONAL
# ==========================================================
def guardar_prediccion_en_dataset(mix, temperatura, tabla_prediccion):
    user_id = obtener_user_id()
    df = cargar_dataset()

    columnas_composicion = _columnas_composicion(df)
    columna_temperatura = detectar_columna_temperatura(df.columns)

    fila = {col: None for col in df.columns}

    # Los elementos que la mezcla NO usa son 0% de esa mezcla,
    # no un dato faltante.
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
    """
    Devuelve (inconsistente: bool, motivo: str|None) para una fila.

    Una fila se marca inconsistente si:
    - le falta algún valor en las columnas de composición (_pct)
      o en la columna de temperatura, o
    - la suma de las columnas de composición no da ~100%.
    """
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
    """
    Carga el dataset maestro desde disco.

    Ahora también detecta si el archivo cambió en disco mediante
    una firma (tamaño + fecha de modificación). Si cambió, vuelve
    a leerlo aunque ya estuviera cargado en memoria.
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
    """
    Convierte una fila (pandas Series) a un dict apto para JSON.
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


def _listar_filas_df(df):
    """
    Arma la estructura {columnas, filas} con detección de
    inconsistencias, para cualquier DataFrame.
    """
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
    """
    Devuelve (columnas, fila) para UNA fila del dataset maestro.
    """
    data = listar_filas_maestro()

    fila = next(
        (f for f in data["filas"] if f["indice"] == indice),
        None
    )

    if fila is None:
        raise ValueError("Fila inexistente")

    return data["columnas"], fila


def listar_filas_usuario():
    """
    Igual que listar_filas_maestro(), pero sobre la copia
    personal del usuario actual.
    """
    df = cargar_dataset()
    return _listar_filas_df(df)


def obtener_fila_usuario(indice):
    """
    Devuelve (columnas, fila) para UNA fila del dataset personal
    del usuario actual.
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
    Edita una fila de la copia personal del usuario actual.
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
    Borra una fila de la copia personal del usuario actual.
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