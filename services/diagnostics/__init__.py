"""
Paquete de diagnóstico de datos.

Modulariza el antiguo services/diagnostico_service.py.

Responsabilidades:
- listado de variables diagnosticables
- cálculo de métricas y outliers
- construcción de motivos de filas sospechosas
- análisis principal de una variable
"""

from .variables import obtener_variables_diagnostico
from .analyzer import analizar_variable
from .metrics import seguro_valor

__all__ = [
    "obtener_variables_diagnostico",
    "analizar_variable",
    "seguro_valor",
]