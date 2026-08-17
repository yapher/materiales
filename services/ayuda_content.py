"""
Fachada de compatibilidad para services/ayuda_content.py.
Este archivo ya no contiene la implementación principal.
La lógica fue movida a services/ayuda/.
Se mantiene para no romper imports existentes en:
- blueprints/ayuda/routes_documentos.py
"""

from .ayuda import (
    contenido_tutorial,
    contenido_modelos,
    contenido_sistema,
)

__all__ = [
    "contenido_tutorial",
    "contenido_modelos",
    "contenido_sistema",
]