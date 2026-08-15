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
# CACHE DATASET POR USUARIO (en memoria del proceso)
# ==========================================================

_datasets = {}
_lock_dataset = threading.Lock()


# ==========================================================
# CREAR DATASET DEL USUARIO (copia la plantilla si no existe)
# ==========================================================

def inicializar_dataset_usuario(user_id=None):
    user_id = user_id or obtener_user_id()
    archivo = archivo_dataset_usuario(user_id)

    if not os.path.exists(archivo):
        logger.info("Creando dataset para usuario %s", user_id)
        shutil.copy(Config.ARCHIVO_DATASET, archivo)

    return archivo


# ==========================================================
# CARGAR DATASET (con cache en memoria por usuario)
# ==========================================================

def cargar_dataset(user_id=None):
    user_id = user_id or obtener_user_id()

    if user_id in _datasets:
        return _datasets[user_id]

    with _lock_dataset:
        if user_id in _datasets:
            return _datasets[user_id]

        archivo = inicializar_dataset_usuario(user_id)

        logger.info("Leyendo dataset usuario %s", user_id)

        df = pd.read_excel(
            archivo,
            sheet_name=Config.HOJA_DATASET
        )

        df = df.dropna(how="all")

        _datasets[user_id] = df

        logger.info(
            "Dataset usuario %s cargado (%s filas)",
            user_id,
            len(df)
        )

        return _datasets[user_id]


# ==========================================================
# RECARGAR DATASET
# ==========================================================

def recargar_dataset():
    user_id = obtener_user_id()
    archivo = inicializar_dataset_usuario(user_id)

    df = pd.read_excel(
        archivo,
        sheet_name=Config.HOJA_DATASET
    )

    df = df.dropna(how="all")

    with _lock_dataset:
        _datasets[user_id] = df

    logger.info("Dataset usuario %s actualizado", user_id)

    return df


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
# GUARDAR UNA PREDICCION COMO FILA NUEVA EN EL DATASET PERSONAL
# ==========================================================

def guardar_prediccion_en_dataset(mix, temperatura, tabla_prediccion):
    from .constants import COLUMNAS

    user_id = obtener_user_id()
    df = cargar_dataset()

    fila = {col: None for col in df.columns}

    # Los elementos que la mezcla NO usa son 0% de esa mezcla,
    # no un dato faltante.
    for col in COLUMNAS:
        if col in fila:
            fila[col] = 0

    for e in mix:
        col = f"{e['elemento']}_pct"

        if col in fila:
            fila[col] = e["pct"]

    if "Temperatura_C" in fila:
        fila["Temperatura_C"] = temperatura

    for item in tabla_prediccion:
        col = item["columna"]

        if col in fila:
            fila[col] = item["prediccion"]

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
_lock_maestro = threading.Lock()

TOLERANCIA_SUMA_PCT = 0.5


def _analizar_fila(fila, columnas_pct):
    """
    Devuelve (inconsistente: bool, motivo: str|None) para una fila.

    Una fila se marca inconsistente si:

    - le falta algún valor en las columnas de composición (_pct)
      o en Temperatura_C, o
    - la suma de las columnas de composición no da ~100%.
    """
    motivos = []

    columnas_obligatorias = columnas_pct + (
        ["Temperatura_C"] if "Temperatura_C" in fila else []
    )

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

    with _lock_maestro:
        if _dataset_maestro is None or forzar:
            logger.info(
                "Leyendo dataset maestro (%s)",
                Config.ARCHIVO_DATASET
            )

            df = pd.read_excel(
                Config.ARCHIVO_DATASET,
                sheet_name=Config.HOJA_DATASET
            )

            df = df.dropna(how="all").reset_index(drop=True)

            _dataset_maestro = df

    return _dataset_maestro


def guardar_dataset_maestro(df):
    global _dataset_maestro

    with _lock_maestro:
        df.to_excel(
            Config.ARCHIVO_DATASET,
            sheet_name=Config.HOJA_DATASET,
            index=False
        )

        _dataset_maestro = df

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
    from .constants import COLUMNAS

    columnas_pct = [c for c in COLUMNAS if c in df.columns]

    filas = []

    for i, fila in df.iterrows():
        inconsistente, motivo = _analizar_fila(fila, columnas_pct)
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