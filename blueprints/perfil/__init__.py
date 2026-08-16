"""
Blueprint de perfil de usuario.
Módulo nuevo: permite al usuario gestionar su cuenta.
Incluye:
- Vista de perfil con datos personales
- Cambio de contraseña
- Gestión de foto de perfil (avatar)

Mantiene la misma convención que los demás blueprints:
mismo patrón de registro modular de rutas.
"""
from flask import Blueprint

perfil_bp = Blueprint(
    "perfil",
    __name__,
    template_folder="templates",
    url_prefix="/perfil",
)

# ==========================================================
# Registro de rutas modulares
# ==========================================================
# Se importan después de crear perfil_bp para que cada módulo
# pueda registrar sus rutas sobre el blueprint.
from . import routes_profile
from . import routes_password
from . import routes_avatar

routes_profile.register(perfil_bp)
routes_password.register(perfil_bp)
routes_avatar.register(perfil_bp)