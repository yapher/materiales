"""
Lógica de gestión de foto de perfil (avatar).

El avatar se guarda en:
    data/users/<username>/avatar.<ext>

Extensiones permitidas: .png, .jpg, .jpeg, .webp
Tamaño máximo: 2 MB
"""
import os
import logging
from utils import (
    obtener_user_id,
    carpeta_usuario,
)

logger = logging.getLogger(__name__)

# Extensiones permitidas para el avatar
EXTENSIONES_PERMITIDAS = {".png", ".jpg", ".jpeg", ".webp"}

# Tamaño máximo: 2 MB
MAX_TAMANO_AVATAR = 2 * 1024 * 1024


def obtener_ruta_avatar(user_id=None):
    """
    Devuelve la ruta del avatar del usuario si existe.
    Busca avatar.png, avatar.jpg, avatar.jpeg, avatar.webp.
    Devuelve None si no existe ninguno.
    """
    user_id = user_id or obtener_user_id()
    carpeta = carpeta_usuario(user_id)
    for ext in EXTENSIONES_PERMITIDAS:
        ruta = os.path.join(carpeta, f"avatar{ext}")
        if os.path.exists(ruta):
            return ruta
    return None


def usuario_tiene_avatar(user_id=None):
    """
    Devuelve True si el usuario tiene foto de perfil.
    Se usa desde el context processor de app.py para el navbar.
    """
    try:
        return obtener_ruta_avatar(user_id) is not None
    except Exception:
        return False


def guardar_avatar_service(file_storage, user_id=None):
    """
    Guarda un nuevo avatar para el usuario.

    Pasos:
    1. Valida extensión y tamaño.
    2. Elimina cualquier avatar anterior.
    3. Guarda el nuevo archivo como avatar.<ext>.

    Lanza ValueError si la validación falla.
    """
    user_id = user_id or obtener_user_id()
    nombre_original = (file_storage.filename or "").strip()

    if not nombre_original:
        raise ValueError("No se seleccionó ningún archivo.")

    # Validar extensión
    extension = os.path.splitext(nombre_original)[1].lower()
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValueError(
            "Solo se permiten imágenes PNG, JPG o WEBP."
        )

    # Validar tamaño
    file_storage.seek(0, os.SEEK_END)
    tamano = file_storage.tell()
    file_storage.seek(0)
    if tamano > MAX_TAMANO_AVATAR:
        raise ValueError(
            "La imagen no puede superar los 2 MB."
        )

    # Eliminar avatar anterior (cualquier extensión)
    _eliminar_archivos_avatar(user_id)

    # Guardar nuevo avatar
    carpeta = carpeta_usuario(user_id)
    ruta_destino = os.path.join(carpeta, f"avatar{extension}")
    file_storage.save(ruta_destino)

    logger.info(
        "Avatar guardado para usuario %s (%s)",
        user_id,
        extension,
    )


def eliminar_avatar_service(user_id=None):
    """
    Elimina la foto de perfil del usuario actual.
    """
    user_id = user_id or obtener_user_id()
    eliminado = _eliminar_archivos_avatar(user_id)
    if eliminado:
        logger.info("Avatar eliminado para usuario %s", user_id)
    else:
        logger.info(
            "No había avatar para eliminar (usuario %s)",
            user_id,
        )


def _eliminar_archivos_avatar(user_id):
    """
    Elimina todos los archivos de avatar del usuario
    (puede haber uno con cada extensión).
    Devuelve True si se eliminó al menos uno.
    """
    carpeta = carpeta_usuario(user_id)
    eliminado = False
    for ext in EXTENSIONES_PERMITIDAS:
        ruta = os.path.join(carpeta, f"avatar{ext}")
        if os.path.exists(ruta):
            os.remove(ruta)
            eliminado = True
    return eliminado