"""
Generación de PDF para el gráfico de densidad vs. temperatura.
Incluye:
- Título y fecha
- Composición de la mezcla
- Gráfico de líneas con regresión lineal
- Puntos reales del dataset
- Estadísticas y ecuación de regresión

El gráfico se dibuja manualmente con primitivas de ReportLab
(Line, Circle, Rect, Polygon, PolyLine) para máxima compatibilidad
con todas las versiones de ReportLab.
"""
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.graphics.shapes import (
    Drawing,
    Rect,
    Line,
    String,
    Circle,
    Polygon,
    PolyLine,
    Group,
)

from .styles import obtener_estilos, obtener_estilo_tabla


def _crear_grafico_densidad(data, ancho=16 * cm, alto=9 * cm):
    """
    Crea el gráfico de densidad vs. temperatura usando primitivas
    de dibujo de ReportLab (sin LinePlot ni makeMarker).

    Devuelve un Drawing listo para insertar en el PDF.
    """
    puntos = data.get("puntos", [])
    regresion = data.get("regresion")
    puntos_reales = data.get("puntos_reales", [])
    puntos_reg_intervalos = data.get("puntos_regresion_intervalos", [])
    parametros = data.get("parametros", {})

    if not puntos:
        return None

    # ==========================================================
    # CONFIGURACIÓN DEL ÁREA DE DIBUJO
    # ==========================================================
    drawing = Drawing(ancho, alto)

    # Fondo
    fondo = Rect(
        0, 0, ancho, alto,
        fillColor=colors.HexColor("#f8f7fc"),
        strokeColor=None,
    )
    drawing.add(fondo)

    # Márgenes del área de gráficos
    margen_izq = 1.8 * cm
    margen_der = 0.5 * cm
    margen_inf = 1.2 * cm
    margen_sup = 0.5 * cm

    area_x_min = margen_izq
    area_x_max = ancho - margen_der
    area_y_min = margen_inf
    area_y_max = alto - margen_sup

    # ==========================================================
    # CÁLCULO DE ESCALAS
    # ==========================================================
    temp_min = parametros.get("temp_min", 1500)
    temp_max = parametros.get("temp_max", 2000)

    # Recopilar todos los valores de densidad para el rango Y
    todas_densidades = [p["densidad"] for p in puntos]
    if puntos_reales:
        todas_densidades += [p["densidad"] for p in puntos_reales]
    if puntos_reg_intervalos:
        todas_densidades += [p["densidad"] for p in puntos_reg_intervalos]
    if regresion and regresion.get("linea"):
        todas_densidades += [p["y"] for p in regresion["linea"]]

    if todas_densidades:
        y_min_datos = min(todas_densidades) - 30
        y_max_datos = max(todas_densidades) + 30
    else:
        y_min_datos = 0
        y_max_datos = 100

    # Recopilar todos los valores de temperatura para el rango X
    todas_temps = [p["temperatura"] for p in puntos]
    if puntos_reales:
        todas_temps += [p["temperatura"] for p in puntos_reales]
    if puntos_reg_intervalos:
        todas_temps += [p["temperatura"] for p in puntos_reg_intervalos]

    if todas_temps:
        x_min_datos = min(todas_temps) - 10
        x_max_datos = max(todas_temps) + 10
    else:
        x_min_datos = temp_min
        x_max_datos = temp_max

    def escala_x(valor):
        """Convierte un valor de temperatura a coordenada X en pixels."""
        if x_max_datos == x_min_datos:
            return (area_x_min + area_x_max) / 2
        return area_x_min + (valor - x_min_datos) / (x_max_datos - x_min_datos) * (area_x_max - area_x_min)

    def escala_y(valor):
        """Convierte un valor de densidad a coordenada Y en pixels."""
        if y_max_datos == y_min_datos:
            return (area_y_min + area_y_max) / 2
        return area_y_min + (valor - y_min_datos) / (y_max_datos - y_min_datos) * (area_y_max - area_y_min)

    # ==========================================================
    # GRID
    # ==========================================================
    grid_color = colors.HexColor("#e0dce8")

    # Grid vertical (temperaturas)
    paso_temp = 100
    t = int(x_min_datos // paso_temp) * paso_temp
    while t <= x_max_datos:
        if t >= x_min_datos:
            px = escala_x(t)
            drawing.add(Line(
                px, area_y_min, px, area_y_max,
                strokeColor=grid_color,
                strokeWidth=0.5,
            ))
            # Etiqueta del eje X
            drawing.add(String(
                px, area_y_min - 12,
                str(int(t)),
                fontName="Helvetica",
                fontSize=7,
                fillColor=colors.HexColor("#555555"),
                textAnchor="middle",
            ))
        t += paso_temp

    # Grid horizontal (densidades)
    rango_y = y_max_datos - y_min_datos
    if rango_y > 500:
        paso_dens = 200
    elif rango_y > 200:
        paso_dens = 100
    elif rango_y > 100:
        paso_dens = 50
    else:
        paso_dens = 25

    d = int(y_min_datos // paso_dens) * paso_dens
    while d <= y_max_datos:
        if d >= y_min_datos:
            py = escala_y(d)
            drawing.add(Line(
                area_x_min, py, area_x_max, py,
                strokeColor=grid_color,
                strokeWidth=0.5,
            ))
            # Etiqueta del eje Y
            drawing.add(String(
                area_x_min - 8, py - 3,
                str(int(d)),
                fontName="Helvetica",
                fontSize=7,
                fillColor=colors.HexColor("#555555"),
                textAnchor="end",
            ))
        d += paso_dens

    # ==========================================================
    # EJES
    # ==========================================================
    eje_color = colors.HexColor("#999999")

    # Eje X
    drawing.add(Line(
        area_x_min, area_y_min, area_x_max, area_y_min,
        strokeColor=eje_color,
        strokeWidth=1,
    ))
    # Eje Y
    drawing.add(Line(
        area_x_min, area_y_min, area_x_min, area_y_max,
        strokeColor=eje_color,
        strokeWidth=1,
    ))

    # Etiqueta del eje X
    drawing.add(String(
        (area_x_min + area_x_max) / 2, 0.2 * cm,
        "Temperatura (K)",
        fontName="Helvetica-Bold",
        fontSize=9,
        fillColor=colors.HexColor("#4a3773"),
        textAnchor="middle",
    ))

    # Etiqueta del eje Y (rotada 90°)
    # En ReportLab, String no tiene atributo 'angle'.
    # Hay que usar un Group con una transformación de rotación.
    grupo_etiqueta_y = Group()
    etiqueta_y_texto = String(
        0, 0,
        "Densidad (kg/m³)",
        fontName="Helvetica-Bold",
        fontSize=9,
        fillColor=colors.HexColor("#4a3773"),
        textAnchor="middle",
    )
    grupo_etiqueta_y.add(etiqueta_y_texto)
    
    # Aplicar rotación de 90° y traslación
    # Transform: (a, b, c, d, e, f) donde:
    # x' = a*x + c*y + e
    # y' = b*x + d*y + f
    # Para rotar 90°: a=0, b=1, c=-1, d=0
    grupo_etiqueta_y.transform = (0, 1, -1, 0, 0.4 * cm, (area_y_min + area_y_max) / 2)
    drawing.add(grupo_etiqueta_y)

    # ==========================================================
    # LÍNEA DE DENSIDAD PREDICHA (verde)
    # ==========================================================
    if len(puntos) >= 2:
        puntos_linea = [
            (escala_x(p["temperatura"]), escala_y(p["densidad"]))
            for p in puntos
        ]
        drawing.add(PolyLine(
            puntos_linea,
            strokeColor=colors.HexColor("#88c999"),
            strokeWidth=2,
        ))

    # Puntos de densidad predicha (círculos verdes)
    for p in puntos:
        px = escala_x(p["temperatura"])
        py = escala_y(p["densidad"])
        drawing.add(Circle(
            px, py, 3,
            fillColor=colors.HexColor("#6bcf80"),
            strokeColor=colors.HexColor("#14101f"),
            strokeWidth=0.5,
        ))

    # ==========================================================
    # LÍNEA DE REGRESIÓN (violeta punteada)
    # ==========================================================
    if regresion and regresion.get("linea") and len(regresion["linea"]) == 2:
        p0 = regresion["linea"][0]
        p1 = regresion["linea"][1]
        drawing.add(Line(
            escala_x(p0["x"]), escala_y(p0["y"]),
            escala_x(p1["x"]), escala_y(p1["y"]),
            strokeColor=colors.HexColor("#6b4fa0"),
            strokeWidth=2,
            strokeDashArray=[6, 4],
        ))

    # ==========================================================
    # PUNTOS DE REGRESIÓN EN INTERVALOS (cuadrados rojos)
    # ==========================================================
    for p in puntos_reg_intervalos:
        px = escala_x(p["temperatura"])
        py = escala_y(p["densidad"])
        tam = 3.5
        drawing.add(Rect(
            px - tam, py - tam, tam * 2, tam * 2,
            fillColor=colors.HexColor("#e07f7f"),
            strokeColor=colors.HexColor("#ffffff"),
            strokeWidth=0.5,
        ))

    # ==========================================================
    # PUNTOS REALES DEL DATASET (triángulos amarillos)
    # ==========================================================
    for p in puntos_reales:
        px = escala_x(p["temperatura"])
        py = escala_y(p["densidad"])
        tam = 5
        # Triángulo apuntando hacia arriba
        drawing.add(Polygon(
            [
                px, py + tam,           # vértice superior
                px - tam, py - tam,     # esquina inferior izquierda
                px + tam, py - tam,     # esquina inferior derecha
            ],
            fillColor=colors.HexColor("#f2d879"),
            strokeColor=colors.HexColor("#c9a832"),
            strokeWidth=1,
        ))

    # ==========================================================
    # LEYENDA
    # ==========================================================
    leyenda_x = area_x_max - 4.5 * cm
    leyenda_y = area_y_max - 0.3 * cm

    items_leyenda = [
        (colors.HexColor("#88c999"), "Densidad predicha"),
        (colors.HexColor("#6b4fa0"), "Regresión lineal"),
        (colors.HexColor("#e07f7f"), "Regresión en intervalos"),
        (colors.HexColor("#f2d879"), "Datos reales"),
    ]

    for i, (color, texto) in enumerate(items_leyenda):
        y_pos = leyenda_y - i * 14
        drawing.add(Rect(
            leyenda_x, y_pos - 4, 8, 8,
            fillColor=color,
            strokeColor=None,
        ))
        drawing.add(String(
            leyenda_x + 12, y_pos - 2,
            texto,
            fontName="Helvetica",
            fontSize=7,
            fillColor=colors.HexColor("#333333"),
        ))

    return drawing


def _tabla_composicion(mix):
    """Crea una tabla con la composición de la mezcla."""
    datos = [["Elemento", "Porcentaje (%)"]]
    for item in mix:
        datos.append([
            item.get("elemento", "—"),
            str(item.get("pct", 0)),
        ])
    # Agregar total
    total = sum(item.get("pct", 0) for item in mix)
    datos.append(["TOTAL", str(round(total, 2))])

    tabla = Table(datos, colWidths=[5 * cm, 4 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a3773")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f5f3fa")]),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8e4f0")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tabla


def _tabla_estadisticas(data):
    """Crea una tabla con las estadísticas de la regresión."""
    stats = data.get("stats", {})
    regresion = data.get("regresion")
    puntos_reales = data.get("puntos_reales", [])
    puntos_reg = data.get("puntos_regresion_intervalos", [])

    datos = [["Métrica", "Valor"]]
    datos.append(["Mínima (kg/m³)", str(stats.get("min", "—"))])
    datos.append(["Máxima (kg/m³)", str(stats.get("max", "—"))])
    datos.append(["Promedio (kg/m³)", str(stats.get("promedio", "—"))])
    datos.append(["Puntos predichos", str(stats.get("cantidad", 0))])

    if regresion:
        datos.append(["R² del ajuste", str(regresion.get("r2", "—"))])
        datos.append(["Pendiente", str(regresion.get("pendiente", "—"))])
        datos.append(["Intercepto", str(regresion.get("intercepto", "—"))])

    datos.append(["Puntos de regresión", str(len(puntos_reg))])
    datos.append(["Datos reales (dataset)", str(len(puntos_reales))])

    tabla = Table(datos, colWidths=[6 * cm, 4 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4a3773")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return tabla


def _tabla_puntos_reales(puntos_reales, max_filas=20):
    """Crea una tabla con los datos reales del dataset."""
    if not puntos_reales:
        return None

    datos = [["#", "Temperatura (K)", "Densidad (kg/m³)"]]
    for i, p in enumerate(puntos_reales[:max_filas], 1):
        datos.append([
            str(i),
            str(p.get("temperatura", "—")),
            str(p.get("densidad", "—")),
        ])

    if len(puntos_reales) > max_filas:
        datos.append(["...", f"({len(puntos_reales) - max_filas} filas más)", "..."])

    tabla = Table(datos, colWidths=[1.5 * cm, 4.5 * cm, 4.5 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#8a7a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fdf9e8")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return tabla


def generar_pdf_grafico_densidad(data, usuario=None):
    """
    Genera un PDF completo con el gráfico de densidad vs. temperatura.

    Parámetros:
    - data: resultado de generar_grafico_densidad()
    - usuario: nombre de usuario (opcional)

    Devuelve: BytesIO con el PDF generado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Densidad vs. Temperatura - Polvos Coladores",
    )

    estilos = obtener_estilos()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ==========================================================
    # HEADER
    # ==========================================================
    subtitulo = f"Generado el {fecha}"
    if usuario:
        subtitulo += f" por {usuario}"

    parametros = data.get("parametros", {})
    rango_texto = (
        f"Rango: {parametros.get('temp_min', 1500)} K → "
        f"{parametros.get('temp_max', 2000)} K, "
        f"intervalo: {parametros.get('intervalo', 20)} K"
    )

    elementos = [
        Paragraph("Densidad vs. Temperatura", estilos["titulo"]),
        Paragraph("Polvos Coladores — Evolución térmica", estilos["subtitulo"]),
        Paragraph(subtitulo, estilos["pie"]),
        Paragraph(rango_texto, estilos["pie"]),
        Spacer(1, 6),
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#4a3773")),
        Spacer(1, 10),
    ]

    # ==========================================================
    # COMPOSICIÓN DE LA MEZCLA
    # ==========================================================
    mix = data.get("_mix_original", [])
    if mix:
        elementos.append(
            Paragraph("Composición del polvo colador", estilos["seccion"])
        )
        elementos.append(_tabla_composicion(mix))
        elementos.append(Spacer(1, 12))

    # ==========================================================
    # GRÁFICO
    # ==========================================================
    elementos.append(
        Paragraph("Gráfico de evolución", estilos["seccion"])
    )

    grafico = _crear_grafico_densidad(data)
    if grafico:
        elementos.append(grafico)
    else:
        elementos.append(
            Paragraph("No se pudo generar el gráfico.", estilos["parrafo"])
        )
    elementos.append(Spacer(1, 12))

    # ==========================================================
    # ECUACIÓN DE REGRESIÓN
    # ==========================================================
    regresion = data.get("regresion")
    if regresion and regresion.get("pendiente") is not None:
        pendiente = regresion["pendiente"]
        intercepto = regresion.get("intercepto", 0)
        signo = "+" if intercepto >= 0 else "−"
        ecuacion_texto = (
            f"<b>Ecuación de regresión lineal:</b> "
            f"ρ = {pendiente:.4f} · T {signo} {abs(intercepto):.2f}"
        )
        r2_texto = f" (R² = {regresion.get('r2', '—')})"
        elementos.append(
            Paragraph(ecuacion_texto + r2_texto, estilos["parrafo"])
        )
        elementos.append(Spacer(1, 10))

    # ==========================================================
    # ESTADÍSTICAS
    # ==========================================================
    elementos.append(
        Paragraph("Estadísticas", estilos["seccion"])
    )
    elementos.append(_tabla_estadisticas(data))
    elementos.append(Spacer(1, 12))

    # ==========================================================
    # DATOS REALES DEL DATASET
    # ==========================================================
    puntos_reales = data.get("puntos_reales", [])
    if puntos_reales:
        elementos.append(
            Paragraph(
                f"Datos reales del dataset ({len(puntos_reales)} puntos)",
                estilos["seccion"]
            )
        )
        tabla_reales = _tabla_puntos_reales(puntos_reales)
        if tabla_reales:
            elementos.append(tabla_reales)
        elementos.append(Spacer(1, 10))

    # ==========================================================
    # LEYENDA
    # ==========================================================
    elementos.append(
        Paragraph("Leyenda del gráfico", estilos["seccion"])
    )
    leyenda_items = [
        "● Línea verde: Densidad predicha por el modelo",
        "┄ Línea violeta punteada: Regresión lineal (ρ = m·T + b)",
        "■ Cuadrados rojos: Valores de la regresión en cada intervalo",
        "▲ Triángulos amarillos: Datos reales medidos del dataset",
    ]
    for item in leyenda_items:
        elementos.append(Paragraph(item, estilos["parrafo"]))

    # ==========================================================
    # BUILD
    # ==========================================================
    doc.build(elementos)
    buffer.seek(0)
    return buffer