"""
Generación de PDF para documentos de ayuda.
"""

import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Preformatted,
)

from .styles import obtener_estilos


def generar_pdf_documento(
    titulo,
    secciones,
    subtitulo=None,
    generado_para=None,
):
    """
    Devuelve un BytesIO con el PDF de un documento de ayuda.
    Este PDF se usa para:
    - tutorial,
    - teoría de modelos,
    - documentación técnica del sistema.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title=titulo,
    )

    estilos = obtener_estilos()
    elementos = [
        Paragraph(escape(titulo), estilos["titulo"])
    ]

    if subtitulo:
        elementos.append(
            Paragraph(escape(subtitulo), estilos["subtitulo"])
        )

    if generado_para:
        elementos.append(
            Paragraph(escape(generado_para), estilos["pie"])
        )

    elementos.append(Spacer(1, 14))

    for seccion in secciones:
        elementos.append(
            Paragraph(escape(seccion["titulo"]), estilos["seccion"])
        )

        for parrafo in seccion.get("parrafos", []):
            elementos.append(
                Paragraph(escape(parrafo), estilos["parrafo"])
            )

        items = seccion.get("items", [])
        if items:
            elementos.append(
                ListFlowable(
                    [
                        ListItem(
                            Paragraph(escape(item), estilos["item"])
                        )
                        for item in items
                    ],
                    bulletType="bullet",
                    start="•",
                    leftIndent=14,
                )
            )
            elementos.append(Spacer(1, 8))

        # Párrafos extra (después de los items)
        for parrafo in seccion.get("parrafos_extra", []):
            elementos.append(
                Paragraph(escape(parrafo), estilos["parrafo"])
            )

        codigo = seccion.get("codigo")
        if codigo:
            elementos.append(
                Preformatted(codigo, estilos["codigo"])
            )
            elementos.append(Spacer(1, 10))

    doc.build(elementos)
    buffer.seek(0)
    return buffer