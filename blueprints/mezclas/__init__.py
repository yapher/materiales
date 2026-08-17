"""
Blueprint de mezclas.
Este paquete reemplaza al antiguo blueprints/mezclas.py.
Mantiene exactamente el mismo nombre de blueprint y los mismos
endpoints, para no romper:
- app.py
- templates
- url_for(...)
- flujo.js
- mezclas.js
- admin
- diagnóstico
"""
from flask import Blueprint

mezclas_bp = Blueprint(
    "mezclas",
    __name__,
)

# ==========================================================
# Registro de rutas modulares
# ==========================================================
# Se importan abajo para evitar problemas de importación
# circular durante el armado del blueprint.
from . import routes_page
from . import routes_training
from . import routes_prediction
from . import routes_dataset
from . import routes_grafico

routes_page.register(mezclas_bp)
routes_training.register(mezclas_bp)
routes_prediction.register(mezclas_bp)
routes_dataset.register(mezclas_bp)
routes_grafico.register(mezclas_bp)