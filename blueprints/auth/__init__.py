"""
Blueprint de autenticación.

Este paquete reemplaza al antiguo blueprints/auth/__init__.py monolítico.

Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:

- app.py
- templates
- url_for(...)
"""

from flask import Blueprint

auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    url_prefix="/auth",
)

from . import routes_forms
from . import routes_oauth

routes_forms.register(auth_bp)
routes_oauth.register(auth_bp)