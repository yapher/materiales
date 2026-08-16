"""
Blueprint de diagnóstico de datos.

Este paquete reemplaza al antiguo blueprints/diagnostico.py monolítico.

Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:

- app.py
- templates
- url_for(...)
"""

from flask import Blueprint

diagnostico_bp = Blueprint(
    "diagnostico",
    __name__,
)

from . import routes_analisis

routes_analisis.register(diagnostico_bp)