"""
Servicio para subir un nuevo dataset maestro desde el panel de Admin.
Responsabilidades:
- validar el archivo subido
- leer el Excel para comprobar que sea válido
- crear backups del dataset maestro anterior
- guardar una copia del archivo seleccionado dentro de DATA_DIR
- dejar como dataset maestro activo:
    DATA_DIR/dataset_maestro_actual.xlsx
- BORRAR el modelo entrenado de TODOS los usuarios
  (porque fue entrenado con datos del maestro anterior)
- Invalidar las caches en memoria de TODOS los usuarios

NOTA: En la arquitectura actual el dataset es GLOBAL (único).
Ya NO se crean copias personales por usuario. Todos los usuarios
leen directamente del maestro.
"""
import os
import shutil
import logging
from datetime import datetime
import pandas as pd
from werkzeug.utils import secure_filename
from config import Config
from utils import obtener_user_id
from utils.auth import _cargar_usuarios
from .excel_service import (
    cargar_dataset_maestro,
    forzar_recarga_usuario,
    obtener_columnas_composicion,
)
from .dataset.cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
)
from .modeling.state import (
    _modelos,
    _estado_entrenamiento,
    _lock_global,
    _lock_estado,
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


def _borrar_modelo_usuario(username):
    """
    Borra modelo.pkl e info_modelo.json de un usuario específico,
    tanto en disco como en las caches de memoria.
    Se usa cuando el dataset maestro cambia y el modelo viejo
    ya no es válido.
    """
    carpeta = os.path.join(Config.USERS_DIR, username)
    ruta_modelo = os.path.join(carpeta, "modelo.pkl")
    ruta_info = os.path.join(carpeta, "info_modelo.json")

    borrados = []
    if os.path.exists(ruta_modelo):
        try:
            os.remove(ruta_modelo)
            borrados.append("modelo.pkl")
        except OSError:
            logger.exception(
                "No se pudo borrar modelo.pkl de %s", username
            )
    if os.path.exists(ruta_info):
        try:
            os.remove(ruta_info)
            borrados.append("info_modelo.json")
        except OSError:
            logger.exception(
                "No se pudo borrar info_modelo.json de %s", username
            )

    # Limpiar caches en memoria
    with _lock_global:
        if username in _modelos:
            _modelos[username] = None
    with _lock_estado:
        _estado_entrenamiento.pop(username, None)

    if borrados:
        logger.info(
            "Modelo borrado para usuario %s: %s",
            username, ", ".join(borrados)
        )
    return len(borrados) > 0


def _invalidar_todas_caches_dataset():
    """
    Invalida TODAS las caches de dataset en memoria.
    Como el dataset es global, basta con limpiar todas las entradas.
    """
    with _lock_dataset:
        _datasets.clear()
        _dataset_firmas.clear()
    logger.info("Caches de dataset invalidadas para todos los usuarios")


def _invalidar_modelos_todos_los_usuarios():
    """
    Borra el modelo entrenado de TODOS los usuarios.
    Devuelve la cantidad de modelos borrados.
    """
    usuarios = _cargar_usuarios()
    modelos_borrados = 0

    for username in usuarios.keys():
        if _borrar_modelo_usuario(username):
            modelos_borrados += 1

    return modelos_borrados


def reemplazar_dataset_maestro(file_storage):
    """
    Reemplaza el dataset maestro por el archivo subido.
    Además:
    - crea backup del maestro anterior en data/backups
    - guarda una copia visible del archivo seleccionado en data/
    - deja activo data/dataset_maestro_actual.xlsx
    - BORRA el modelo de TODOS los usuarios
    - Invalida TODAS las caches de dataset en memoria
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

    # Validación mínima: columnas de composición en A-K.
    columnas_pct = obtener_columnas_composicion(df)
    if not columnas_pct:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise ValueError(
            "El archivo no contiene columnas de composición terminadas "
            "en '_pct' dentro de las primeras 11 columnas (A-K). "
            "Revisá que sea el dataset correcto."
        )

    backups = _directorio_backups()

    # Backup del dataset maestro actualmente configurado.
    if os.path.exists(Config.ARCHIVO_DATASET):
        respaldo_maestro = os.path.join(
            backups,
            f"dataset_maestro_anterior_{timestamp}.xlsx"
        )
        try:
            shutil.copy2(Config.ARCHIVO_DATASET, respaldo_maestro)
        except OSError:
            logger.exception(
                "No se pudo crear backup del maestro anterior"
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
        try:
            shutil.copy2(destino, respaldo_actual)
        except OSError:
            logger.exception(
                "No se pudo crear backup del dataset_maestro_actual"
            )

    # Copia visible del archivo seleccionado dentro de DATA_DIR.
    copia_visible = None
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
        shutil.copyfile(tmp_path, copia_visible)
    except Exception:
        logger.exception(
            "No se pudo crear la copia visible del dataset en DATA_DIR"
        )
        copia_visible = None

    try:
        # Guardar el dataset activo.
        shutil.copyfile(tmp_path, destino)

        # Actualizar la configuración en memoria para que el sistema
        # use inmediatamente el nuevo dataset.
        Config.ARCHIVO_DATASET = destino

        # ===========================================================
        # INVALIDAR CACHES Y BORRAR MODELOS DE TODOS LOS USUARIOS
        # ===========================================================
        # 1. Invalidar todas las caches de dataset en memoria
        _invalidar_todas_caches_dataset()

        # 2. Borrar modelos de todos los usuarios
        modelos_borrados = _invalidar_modelos_todos_los_usuarios()

        # 3. Forzar recarga del maestro en memoria
        cargar_dataset_maestro(forzar=True)

        # 4. Forzar recarga del usuario actual (el admin)
        df_usuario = forzar_recarga_usuario(user_id)

        usuarios = _cargar_usuarios()
        usuarios_afectados = len(usuarios)

        logger.info(
            "Dataset maestro reemplazado por %s (usuario %s). "
            "Activo: %s. Usuarios afectados: %s. "
            "Modelos borrados: %s.",
            nombre_original,
            user_id,
            destino,
            usuarios_afectados,
            modelos_borrados,
        )

        return {
            "filas": len(df_usuario),
            "columnas": len(df_usuario.columns),
            "archivo_activo": destino,
            "copia_visible": copia_visible,
            "usuarios_actualizados": usuarios_afectados,
            "modelos_borrados": modelos_borrados,
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)