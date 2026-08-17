"""
Paquete de contenido de ayuda.
Modulariza el antiguo services/ayuda_content.py.
Responsabilidades:
- contenido del tutorial de uso
- contenido de la teoría de modelos
- contenido de la documentación técnica del sistema
"""

from .tutorial import contenido_tutorial
from .modelos import contenido_modelos
from .sistema import contenido_sistema

__all__ = [
    "contenido_tutorial",
    "contenido_modelos",
    "contenido_sistema",
]