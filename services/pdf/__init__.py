"""
Paquete de generación de PDF.

Modulariza el antiguo services/pdf_service.py.

Responsabilidades:
- estilos base de PDF
- documentos de ayuda
- PDF de predicción
- PDF de filas de dataset
"""

from .document import generar_pdf_documento
from .prediction import generar_pdf_prediccion
from .dataset_row import generar_pdf_fila_dataset

__all__ = [
    "generar_pdf_documento",
    "generar_pdf_prediccion",
    "generar_pdf_fila_dataset",
]