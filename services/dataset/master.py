"""
Dataset maestro (global).
Es el ÚNICO dataset del sistema.
Solo el admin lo edita.
Cualquier edición invalida el modelo entrenado de TODOS los usuarios.
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

# Clave única para el dataset global en la cache del loader
_GLOBAL_KEY = "__global__"


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
    También invalida la cache del loader global.
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

        # Invalidar la cache del loader global
        # _GLOBAL_KEY está definida arriba en este mismo módulo.
        from .cache import _datasets, _dataset_firmas
        if _GLOBAL_KEY in _datasets:
            del _datasets[_GLOBAL_KEY]
        if _GLOBAL_KEY in _dataset_firmas:
            del _dataset_firmas[_GLOBAL_KEY]

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
    IMPORTANTE: el caller debe borrar el modelo después.
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
    IMPORTANTE: el caller debe borrar el modelo después.
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
    IMPORTANTE: el caller debe borrar el modelo después.
    """
    df = cargar_dataset_maestro()
    if indice_invalido := (df is None or df.empty):
        raise ValueError("Dataset vacío, no se puede agregar fila")

    # Construir la fila nueva con todas las columnas del df.
    # Valores no enviados quedan como None.
    nueva = {}
    for col in df.columns:
        nueva[col] = valores.get(col) if col in valores else None

    # Usar .loc[len(df)] para agregar una fila sin FutureWarning
    # de pd.concat con columnas all-NA.
    nueva_idx = len(df)
    for col, val in nueva.items():
        df.loc[nueva_idx, col] = val

    guardar_dataset_maestro(df)
    return df