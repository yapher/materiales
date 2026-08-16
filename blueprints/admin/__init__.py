"""
Blueprint de administración.

Este paquete reemplaza al antiguo blueprints/admin/__init__.py
monolítico.

Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:

- app.py
- templates/admin/*
- url_for(...)
"""

from flask import Blueprint


admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    url_prefix="/admin",
)


# ==========================================================
# Registro de rutas modulares
# ==========================================================
# Se importan después de crear admin_bp para que cada módulo
# pueda registrar sus rutas sobre el blueprint.
from . import routes_general
from . import routes_dataset
from . import routes_users


routes_general.register(admin_bp)
routes_dataset.register(admin_bp)
routes_users.register(admin_bp)