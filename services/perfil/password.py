"""
Lógica de cambio de contraseña del perfil de usuario.
"""
import logging
from utils import (
    obtener_user_id,
    verificar_password,
    cambiar_password,
)

logger = logging.getLogger(__name__)


def cambiar_password_service(password_actual, password_nueva, password_nueva2):
    """
    Cambia la contraseña del usuario actual.

    Valida:
    1. Que el usuario tenga contraseña (no sea login social).
    2. Que la contraseña actual sea correcta.
    3. Que la nueva contraseña tenga al menos 6 caracteres.
    4. Que las dos contraseñas nuevas coincidan.

    Lanza ValueError si alguna validación falla.
    """
    user_id = obtener_user_id()

    # Verificar contraseña actual
    if not verificar_password(user_id, password_actual):
        raise ValueError("La contraseña actual es incorrecta.")

    # Validar longitud mínima
    if len(password_nueva) < 6:
        raise ValueError(
            "La nueva contraseña debe tener al menos 6 caracteres."
        )

    # Verificar que coincidan las dos contraseñas nuevas
    if password_nueva != password_nueva2:
        raise ValueError("Las contraseñas nuevas no coinciden.")

    # Cambiar la contraseña
    cambiar_password(user_id, password_nueva)
    logger.info("Usuario %s cambió su contraseña", user_id)