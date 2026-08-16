"""
Servicio para subir un nuevo dataset maestro desde el panel de Admin.

Responsabilidades:
- validar el archivo subido
- leer el Excel para comprobar que sea válido
- crear backups del dataset maestro anterior y del dataset personal actual
- guardar una copia del archivo seleccionado dentro de DATA_DIR
- dejar como dataset maestro activo:
  DATA_DIR/dataset_maestro_actual.xlsx
- sobreescribir el dataset personal del usuario actual con el nuevo maestro
- forzar la recarga del dataset maestro y del dataset personal en memoria

IMPORTANTE:
Este servicio NO borra el modelo. Eso lo hace el blueprint de admin
llamando a reset_modelo_service() después de confirmar la subida.
"""

import os
import shutil
import logging
from datetime import datetime

import pandas as pd
from werkzeug.utils import secure_filename

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario

from .excel_service import (
    cargar_dataset_maestro,
    forzar_recarga_usuario,
    obtener_columnas_composicion,
)

logger = logging.getLogger(__name__)


def _asegurar_directorio(ruta):
    os.makedirs(ruta, exist_ok=True)
    return ruta


def _directorio_backups():
    return _asegurar_directorio(
        os.path.join(Config.DATA_DIR, "backups")
    )


def _directorio_tmp():
    return _asegurar_directorio(
        os.path.join(Config.DATA_DIR, "tmp")
    )


def _extension_permitida(nombre):
    """
    Solo aceptamos Excel moderno.
    .xls viejo no está soportado por el stack actual.
    """
    return nombre.lower().endswith((".xlsx", ".xlsm"))


def reemplazar_dataset_maestro(file_storage):
    """
    Reemplaza el dataset maestro por el archivo subido.

    Además:
    - crea backup del maestro anterior en data/backups
    - crea backup del dataset personal actual del usuario
    - guarda una copia visible del archivo seleccionado en data/
    - deja activo data/dataset_maestro_actual.xlsx
    - sobreescribe el dataset personal del usuario actual
    - fuerza recarga del dataset personal en memoria
    """
    user_id = obtener_user_id()

    nombre_original = (file_storage.filename or "").strip()

    if not nombre_original:
        raise ValueError("No se seleccionó ningún archivo.")

    if not _extension_permitida(nombre_original):
        raise ValueError(
            "Solo se permiten archivos Excel .xlsx o .xlsm."
        )

    extension = os.path.splitext(nombre_original)[1].lower() or ".xlsx"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    tmp_dir = _directorio_tmp()
    tmp_path = os.path.join(
        tmp_dir,
        f"dataset_subido_{timestamp}{extension}"
    )

    # Guardar temporalmente el archivo subido.
    file_storage.save(tmp_path)

    # Validar que el archivo sea legible y tenga la hoja esperada.
    try:
        df = pd.read_excel(
            tmp_path,
            sheet_name=Config.HOJA_DATASET
        )
        df = df.dropna(how="all")
    except Exception as error:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        logger.exception(
            "No se pudo leer el dataset subido por %s",
            user_id
        )

        raise ValueError(
            f"No se pudo leer el archivo como dataset. "
            f"Debe ser un Excel válido con la hoja '{Config.HOJA_DATASET}'."
        ) from error

    if df.empty or len(df.columns) == 0:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        raise ValueError(
            "El Excel está vacío o no contiene filas de datos."
        )

    # Validación mínima: deben existir columnas de composición en el
    # bloque inicial A-K. No sirve cualquier columna *_pct en cualquier
    # posición, porque de la columna L en adelante pueden existir
    # variables objetivo que también terminen en _pct.
    columnas_pct = obtener_columnas_composicion(df)

    if not columnas_pct:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

        raise ValueError(
            "El archivo no contiene columnas de composición terminadas en '_pct' "
            "dentro de las primeras 11 columnas (A-K). "
            "Revisá que sea el dataset correcto."
        )

    backups = _directorio_backups()

    # Backup del dataset maestro actualmente configurado.
    if os.path.exists(Config.ARCHIVO_DATASET):
        respaldo_maestro = os.path.join(
            backups,
            f"dataset_maestro_anterior_{timestamp}.xlsx"
        )
        shutil.copy2(
            Config.ARCHIVO_DATASET,
            respaldo_maestro
        )

    # Ruta activa del nuevo dataset maestro.
    destino = getattr(
        Config,
        "ARCHIVO_DATASET_SUBIDO",
        os.path.join(Config.DATA_DIR, "dataset_maestro_actual.xlsx")
    )

    # Si ya existía un dataset_maestro_actual.xlsx, backup.
    if (
        os.path.exists(destino)
        and os.path.abspath(destino) != os.path.abspath(Config.ARCHIVO_DATASET)
    ):
        respaldo_actual = os.path.join(
            backups,
            f"dataset_maestro_actual_anterior_{timestamp}.xlsx"
        )
        shutil.copy2(
            destino,
            respaldo_actual
        )

    # Copia visible del archivo seleccionado dentro de DATA_DIR.
    # Es opcional: si falla, no debería frenar la carga del dataset activo.
    try:
        nombre_seguro = secure_filename(nombre_original)

        if not nombre_seguro:
            nombre_seguro = f"dataset_subido_{timestamp}{extension}"

        if not nombre_seguro.lower().endswith(extension):
            nombre_seguro += extension

        base, ext = os.path.splitext(nombre_seguro)

        if len(base) > 80:
            base = base[:80]

        nombre_seguro = base + ext

        copia_visible = os.path.join(
            Config.DATA_DIR,
            f"{timestamp}_{nombre_seguro}"
        )

        shutil.copyfile(
            tmp_path,
            copia_visible
        )
    except Exception:
        logger.exception(
            "No se pudo crear la copia visible del dataset en DATA_DIR"
        )
        copia_visible = None

    try:
        # Guardar el dataset activo.
        shutil.copyfile(
            tmp_path,
            destino
        )

        # Actualizar la configuración en memoria para que el sistema
        # use inmediatamente el nuevo dataset.
        Config.ARCHIVO_DATASET = destino

        # Sobreescribir el dataset personal del usuario actual.
        archivo_personal = archivo_dataset_usuario(user_id)

        os.makedirs(
            os.path.dirname(archivo_personal),
            exist_ok=True
        )

        if os.path.exists(archivo_personal):
            respaldo_personal = os.path.join(
                backups,
                f"dataset_personal_{user_id}_{timestamp}.xlsx"
            )
            shutil.copy2(
                archivo_personal,
                respaldo_personal
            )

        shutil.copyfile(
            destino,
            archivo_personal
        )

        # Forzar recarga del maestro en memoria.
        cargar_dataset_maestro(forzar=True)

        # Forzar recarga del dataset personal del usuario actual.
        # Esto es lo que hace que "Mi dataset" muestre el nuevo.
        df_usuario = forzar_recarga_usuario(user_id)

        logger.info(
            "Dataset maestro reemplazado por %s (usuario %s). Activo: %s",
            nombre_original,
            user_id,
            destino
        )

        return {
            "filas": len(df_usuario),
            "columnas": len(df_usuario.columns),
            "archivo_activo": destino,
            "copia_visible": copia_visible,
        }

    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)