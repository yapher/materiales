"""
Lógica de actualización de datos personales del perfil.
"""
import logging
from utils import (
    obtener_user_id,
    actualizar_perfil,
)

logger = logging.getLogger(__name__)


def actualizar_datos_service(email=None, nombre=None):
    """
    Actualiza los datos personales del usuario actual.
    Campos editables: email, nombre.

    Valida:
    - Formato básico de email (si se envía).
    - Longitud máxima de nombre.

    Lanza ValueError si alguna validación falla.
    """
    user_id = obtener_user_id()

    # Validación básica de email
    if email is not None and email.strip():
        email = email.strip()
        if "@" not in email or "." not in email.split("@")[-1]:
            raise ValueError("El email no tiene un formato válido.")
    else:
        email = None

    # Validación de nombre
    if nombre is not None:
        nombre = nombre.strip()
        if len(nombre) > 60:
            raise ValueError(
                "El nombre no puede tener más de 60 caracteres."
            )
        if not nombre:
            nombre = None

    # Guardar
    actualizar_perfil(user_id, email=email, nombre=nombre)
    logger.info("Usuario %s actualizó sus datos personales", user_id)

    return {
        "email": email,
        "nombre": nombre,
    }