"""
Blueprint de ayuda.

Este paquete reemplaza al antiguo blueprints/ayuda/__init__.py monolítico.

Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:

- app.py
- templates
- url_for(...)
"""

from flask import Blueprint

ayuda_bp = Blueprint(
    "ayuda",
    __name__,
    template_folder="templates",
    url_prefix="/ayuda",
)

from . import routes_documentos

routes_documentos.register(ayuda_bp)