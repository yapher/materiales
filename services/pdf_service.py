"""
Fachada de compatibilidad para services/pdf_service.py.
Este archivo ya no contiene la implementación principal.
La lógica fue movida a services/pdf/.
Se mantiene para no romper imports existentes en:
- blueprints/ayuda/__init__.py
- blueprints/mezclas.py
- blueprints/admin/__init__.py
"""
from .pdf import (
    generar_pdf_documento,
    generar_pdf_prediccion,
    generar_pdf_fila_dataset,
    generar_pdf_grafico_densidad,
)

# Compatibilidad con nombres privados viejos, por si algún
# módulo interno los llegaba a importar.
from .pdf.styles import (
    obtener_estilos as _estilos,
    obtener_estilo_tabla as _estilo_tabla,
)

__all__ = [
    "generar_pdf_documento",
    "generar_pdf_prediccion",
    "generar_pdf_fila_dataset",
    "generar_pdf_grafico_densidad",
    "_estilos",
    "_estilo_tabla",
]