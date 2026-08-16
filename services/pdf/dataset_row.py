"""
Generación de PDF para una fila del dataset.
"""

import io

from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
)

from .styles import (
    obtener_estilos,
    obtener_estilo_tabla,
)


def generar_pdf_fila_dataset(
    titulo,
    indice,
    columnas,
    valores,
    inconsistente=False,
    motivo=None,
    generado_para=None,
):
    """
    PDF de UNA fila del dataset (maestro o personal):

    - todas sus columnas con su valor,
    - aviso destacado si está marcada como inconsistente.
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

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    subtitulo = f"Fila #{indice} — Generado el {fecha}"

    elementos = [
        Paragraph(escape(titulo), estilos["titulo"]),
        Paragraph(escape(subtitulo), estilos["subtitulo"]),
    ]

    if generado_para:
        elementos.append(
            Paragraph(escape(generado_para), estilos["pie"])
        )

        elementos.append(Spacer(1, 10))

    if inconsistente:
        estilo_aviso = ParagraphStyle(
            "Aviso",
            parent=estilos["parrafo"],
            textColor=colors.HexColor("#b35c00"),
            backColor=colors.HexColor("#fbeee0"),
            borderPadding=8,
            spaceAfter=14,
        )

        elementos.append(
            Paragraph(
                escape(f"⚠ Fila inconsistente: {motivo}"),
                estilo_aviso
            )
        )

    datos = [["Columna", "Valor"]] + [
        [
            col,
            "—" if valores.get(col) is None else str(valores.get(col))
        ]
        for col in columnas
    ]

    tabla = Table(
        datos,
        colWidths=[7 * cm, 6 * cm]
    )

    tabla.setStyle(obtener_estilo_tabla())
    elementos.append(tabla)

    doc.build(elementos)

    buffer.seek(0)

    return buffer