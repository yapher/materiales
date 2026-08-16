"""
Blueprint de la página de inicio.

Este paquete reemplaza al antiguo blueprints/home/__init__.py monolítico.

Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:

- app.py
- templates
- url_for(...)
"""

from flask import Blueprint

home_bp = Blueprint(
    "home",
    __name__,
    template_folder="templates",
)

from . import routes_pages

routes_pages.register(home_bp)