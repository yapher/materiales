"""
Fachada de compatibilidad para services/diagnostico_service.py.

Este archivo ya no contiene la implementación principal.
La lógica fue movida a services/diagnostics/.

Se mantiene para no romper imports existentes en:

- blueprints/diagnostico.py
"""

from .diagnostics import (
    obtener_variables_diagnostico,
    analizar_variable,
    seguro_valor,
)

__all__ = [
    "obtener_variables_diagnostico",
    "analizar_variable",
    "seguro_valor",
]