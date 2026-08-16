"""
Estilos base para generación de PDF con ReportLab.
"""

from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle,
)

from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import TableStyle


def obtener_estilos():
    """
    Devuelve los estilos base usados por los PDF del sistema.
    """
    base = getSampleStyleSheet()

    return {
        "titulo": ParagraphStyle(
            "TituloDoc",
            parent=base["Title"],
            fontSize=20,
            spaceAfter=6,
            textColor=colors.HexColor("#2f2547"),
        ),

        "subtitulo": ParagraphStyle(
            "SubtituloDoc",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.grey,
            spaceAfter=20,
        ),

        "seccion": ParagraphStyle(
            "Seccion",
            parent=base["Heading2"],
            fontSize=13.5,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#4a3773"),
        ),

        "parrafo": ParagraphStyle(
            "Parrafo",
            parent=base["Normal"],
            fontSize=10.3,
            leading=15,
            spaceAfter=7,
            alignment=TA_LEFT,
        ),

        "item": ParagraphStyle(
            "Item",
            parent=base["Normal"],
            fontSize=10.3,
            leading=14,
        ),

        "codigo": ParagraphStyle(
            "Codigo",
            parent=base["Code"],
            fontSize=8,
            leading=10.5,
            backColor=colors.HexColor("#f2f0f7"),
            borderPadding=6,
        ),

        "pie": ParagraphStyle(
            "Pie",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.grey,
        ),
    }


def obtener_estilo_tabla():
    """
    Devuelve el estilo visual usado por las tablas de los PDF.
    """
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a3773")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        (
            "ROWBACKGROUNDS",
            (0, 1),
            (-1, -1),
            [colors.white, colors.HexColor("#f5f3fa")]
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ])