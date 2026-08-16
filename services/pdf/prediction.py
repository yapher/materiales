"""
Generación de PDF para una predicción de mezcla.
"""

import io

from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

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


def generar_pdf_prediccion(
    mix,
    temperatura,
    tabla_prediccion,
    usuario=None,
):
    """
    PDF de UNA predicción puntual:

    - composición de la mezcla,
    - temperatura del proceso,
    - tabla de propiedades predichas.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Predicción de mezcla",
    )

    estilos = obtener_estilos()

    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    subtitulo = f"Generado el {fecha}"

    if usuario:
        subtitulo += f" por {usuario}"

    elementos = [
        Paragraph("Predicción de mezcla", estilos["titulo"]),
        Paragraph(escape(subtitulo), estilos["subtitulo"]),
    ]

    # ----------------------------------------------------------
    # Composición de la mezcla
    # ----------------------------------------------------------
    elementos.append(
        Paragraph("Composición de la mezcla", estilos["seccion"])
    )

    datos_mix = [["Elemento", "Porcentaje"]] + [
        [m["elemento"], f"{m['pct']}%"]
        for m in mix
    ]

    tabla_mix = Table(
        datos_mix,
        colWidths=[7 * cm, 4 * cm]
    )

    tabla_mix.setStyle(obtener_estilo_tabla())
    elementos.append(tabla_mix)

    elementos.append(Spacer(1, 6))

    # La UI actualmente usa temperatura en K.
    # Si en algún momento el dataset usa otra unidad,
    # esta línea se puede parametrizar.
    elementos.append(
        Paragraph(
            f"Temperatura del proceso: {temperatura} K",
            estilos["parrafo"]
        )
    )

    elementos.append(Spacer(1, 8))

    # ----------------------------------------------------------
    # Propiedades predichas
    # ----------------------------------------------------------
    elementos.append(
        Paragraph("Propiedades predichas", estilos["seccion"])
    )

    datos_pred = [["Variable", "Predicción"]] + [
        [p["columna"], str(p["prediccion"])]
        for p in tabla_prediccion
    ]

    tabla_pred = Table(
        datos_pred,
        colWidths=[7 * cm, 4 * cm]
    )

    tabla_pred.setStyle(obtener_estilo_tabla())
    elementos.append(tabla_pred)

    doc.build(elementos)

    buffer.seek(0)

    return buffer