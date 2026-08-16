"""
Paquete de servicios de perfil de usuario.
Modulariza la lógica de:
- Cambio de contraseña
- Actualización de datos personales
- Gestión de foto de perfil (avatar)

Sigue la misma convención que services/dataset/, services/modeling/, etc.
"""
from .password import cambiar_password_service
from .datos import actualizar_datos_service
from .avatar import (
    guardar_avatar_service,
    eliminar_avatar_service,
    obtener_ruta_avatar,
    usuario_tiene_avatar,
)

__all__ = [
    "cambiar_password_service",
    "actualizar_datos_service",
    "guardar_avatar_service",
    "eliminar_avatar_service",
    "obtener_ruta_avatar",
    "usuario_tiene_avatar",
]