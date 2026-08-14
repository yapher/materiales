"""
Genera PDFs a partir de contenido estructurado (lista de "secciones"),
usando ReportLab. Se usa para exportar los documentos del menú de
Ayuda (tutorial, teoría de los modelos, documentación técnica interna).

Formato esperado de cada sección (dict):
    {
        "titulo": "Nombre de la sección",
        "parrafos": ["texto...", "texto..."],   # opcional
        "items": ["punto 1", "punto 2"],         # opcional, lista con viñetas
        "codigo": "texto preformateado...",      # opcional, bloque de código
    }
"""
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    ListFlowable,
    ListItem,
    Preformatted,
    Table,
    TableStyle,
)


def _estilos():
    base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloDoc", parent=base["Title"], fontSize=20, spaceAfter=6,
            textColor=colors.HexColor("#2f2547"),
        ),
        "subtitulo": ParagraphStyle(
            "SubtituloDoc", parent=base["Normal"], fontSize=11,
            textColor=colors.grey, spaceAfter=20,
        ),
        "seccion": ParagraphStyle(
            "Seccion", parent=base["Heading2"], fontSize=13.5,
            spaceBefore=16, spaceAfter=8, textColor=colors.HexColor("#4a3773"),
        ),
        "parrafo": ParagraphStyle(
            "Parrafo", parent=base["Normal"], fontSize=10.3, leading=15,
            spaceAfter=7, alignment=TA_LEFT,
        ),
        "item": ParagraphStyle(
            "Item", parent=base["Normal"], fontSize=10.3, leading=14,
        ),
        "codigo": ParagraphStyle(
            "Codigo", parent=base["Code"], fontSize=8, leading=10.5,
            backColor=colors.HexColor("#f2f0f7"), borderPadding=6,
        ),
        "pie": ParagraphStyle(
            "Pie", parent=base["Normal"], fontSize=8, textColor=colors.grey,
        ),
    }


def generar_pdf_documento(titulo, secciones, subtitulo=None, generado_para=None):
    """
    Devuelve un BytesIO con el PDF ya armado, listo para mandar con
    send_file (ver blueprints/ayuda/__init__.py).
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

    e = _estilos()
    elementos = [Paragraph(escape(titulo), e["titulo"])]

    if subtitulo:
        elementos.append(Paragraph(escape(subtitulo), e["subtitulo"]))
    if generado_para:
        elementos.append(Paragraph(escape(generado_para), e["pie"]))
        elementos.append(Spacer(1, 14))

    for seccion in secciones:
        elementos.append(Paragraph(escape(seccion["titulo"]), e["seccion"]))

        for parrafo in seccion.get("parrafos", []):
            elementos.append(Paragraph(escape(parrafo), e["parrafo"]))

        items = seccion.get("items", [])
        if items:
            elementos.append(ListFlowable(
                [ListItem(Paragraph(escape(item), e["item"])) for item in items],
                bulletType="bullet",
                start="•",
                leftIndent=14,
            ))
            elementos.append(Spacer(1, 8))

        codigo = seccion.get("codigo")
        if codigo:
            elementos.append(Preformatted(codigo, e["codigo"]))
            elementos.append(Spacer(1, 10))

    doc.build(elementos)
    buffer.seek(0)
    return buffer


def _estilo_tabla():
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a3773")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ])


def generar_pdf_prediccion(mix, temperatura, tabla_prediccion, usuario=None):
    """
    PDF de UNA predicción puntual: composición de la mezcla, temperatura
    del proceso, y la tabla de propiedades predichas.
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

    e = _estilos()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    subtitulo = f"Generado el {fecha}" + (f" por {usuario}" if usuario else "")

    elementos = [
        Paragraph("Predicción de mezcla", e["titulo"]),
        Paragraph(escape(subtitulo), e["subtitulo"]),
    ]

    elementos.append(Paragraph("Composición de la mezcla", e["seccion"]))
    datos_mix = [["Elemento", "Porcentaje"]] + [
        [m["elemento"], f"{m['pct']}%"] for m in mix
    ]
    tabla_mix = Table(datos_mix, colWidths=[7 * cm, 4 * cm])
    tabla_mix.setStyle(_estilo_tabla())
    elementos.append(tabla_mix)
    elementos.append(Spacer(1, 6))

    elementos.append(Paragraph(f"Temperatura del proceso: {temperatura} °C", e["parrafo"]))
    elementos.append(Spacer(1, 8))

    elementos.append(Paragraph("Propiedades predichas", e["seccion"]))
    datos_pred = [["Variable", "Predicción"]] + [
        [p["columna"], str(p["prediccion"])] for p in tabla_prediccion
    ]
    tabla_pred = Table(datos_pred, colWidths=[7 * cm, 4 * cm])
    tabla_pred.setStyle(_estilo_tabla())
    elementos.append(tabla_pred)

    doc.build(elementos)
    buffer.seek(0)
    return buffer


def generar_pdf_fila_dataset(titulo, indice, columnas, valores, inconsistente=False, motivo=None, generado_para=None):
    """
    PDF de UNA fila del dataset (maestro o personal): todas sus columnas
    con su valor, y un aviso destacado si esta marcada como inconsistente.
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

    e = _estilos()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    subtitulo = f"Fila #{indice} — Generado el {fecha}"

    elementos = [Paragraph(escape(titulo), e["titulo"]), Paragraph(escape(subtitulo), e["subtitulo"])]

    if generado_para:
        elementos.append(Paragraph(escape(generado_para), e["pie"]))
        elementos.append(Spacer(1, 10))

    if inconsistente:
        estilo_aviso = ParagraphStyle(
            "Aviso", parent=e["parrafo"],
            textColor=colors.HexColor("#b35c00"),
            backColor=colors.HexColor("#fbeee0"),
            borderPadding=8, spaceAfter=14,
        )
        elementos.append(Paragraph(escape(f"⚠ Fila inconsistente: {motivo}"), estilo_aviso))

    datos = [["Columna", "Valor"]] + [
        [col, "—" if valores.get(col) is None else str(valores.get(col))]
        for col in columnas
    ]
    tabla = Table(datos, colWidths=[7 * cm, 6 * cm])
    tabla.setStyle(_estilo_tabla())
    elementos.append(tabla)

    doc.build(elementos)
    buffer.seek(0)
    return buffer
