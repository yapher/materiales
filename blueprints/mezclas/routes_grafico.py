"""
Rutas para la generación de gráficos a partir del modelo entrenado.
Incluye:
- Gráfico de densidad vs. temperatura (evolución térmica)
- Exportación del gráfico de densidad a PDF
- Gráfico de regresión lineal (predicción vs. real)
- Listado de variables disponibles para regresión
"""
import logging
from flask import (
    request,
    jsonify,
    send_file,
)
from services.mezcla_service import generar_grafico_densidad
from services.modeling.regresion import (
    generar_grafico_regresion,
    listar_variables_regresion,
)
from services.pdf_service import generar_pdf_grafico_densidad
from utils import (
    manejar_errores_json,
    login_required_json,
    usuario_actual,
)

logger = logging.getLogger(__name__)


def register(bp):
    """
    Registra las rutas de gráficos sobre el blueprint de mezclas.
    """

    # ==========================================================
    # GRÁFICO DENSIDAD VS. TEMPERATURA
    # ==========================================================
    @bp.route("/mezclas/grafico_densidad", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def grafico_densidad():
        """
        Genera puntos de densidad predicha en función de la
        temperatura, manteniendo la composición fija.

        Body JSON esperado:
        {
            "mix": [...],
            "temp_min": 1500,
            "temp_max": 2000,
            "intervalo": 20
        }
        """
        data = request.get_json(silent=True) or {}
        mix = data.get("mix", [])
        temp_min = data.get("temp_min")
        temp_max = data.get("temp_max")
        intervalo = data.get("intervalo")

        resultado = generar_grafico_densidad(
            mix=mix,
            temp_min=temp_min,
            temp_max=temp_max,
            intervalo=intervalo,
        )
        return jsonify({
            "ok": True,
            **resultado,
        })

    # ==========================================================
    # EXPORTAR GRÁFICO DENSIDAD A PDF
    # ==========================================================
    @bp.route("/mezclas/grafico_densidad/pdf", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def grafico_densidad_pdf():
        """
        Genera un PDF con el gráfico de densidad vs. temperatura.

        Body JSON esperado (mismo que /mezclas/grafico_densidad):
        {
            "mix": [...],
            "temp_min": 1500,
            "temp_max": 2000,
            "intervalo": 20
        }
        """
        data = request.get_json(silent=True) or {}
        mix = data.get("mix", [])
        temp_min = data.get("temp_min")
        temp_max = data.get("temp_max")
        intervalo = data.get("intervalo")

        # Generar los datos del gráfico
        resultado = generar_grafico_densidad(
            mix=mix,
            temp_min=temp_min,
            temp_max=temp_max,
            intervalo=intervalo,
        )

        # Agregar la mezcla original al resultado para el PDF
        resultado["_mix_original"] = mix

        # Obtener usuario actual
        usuario = usuario_actual()
        nombre_usuario = usuario["username"] if usuario else None

        # Generar el PDF
        buffer = generar_pdf_grafico_densidad(
            resultado,
            usuario=nombre_usuario,
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="densidad_vs_temperatura.pdf",
        )

    # ==========================================================
    # VARIABLES DISPONIBLES PARA REGRESIÓN LINEAL
    # ==========================================================
    @bp.route("/mezclas/grafico_regresion/variables")
    @login_required_json
    @manejar_errores_json
    def grafico_regresion_variables():
        """
        Devuelve la lista de variables entrenadas en el modelo
        del usuario actual, para poblar el select del modal
        de regresión lineal.
        """
        variables = listar_variables_regresion()
        return jsonify({
            "ok": True,
            "variables": variables,
        })

    # ==========================================================
    # GRÁFICO REGRESIÓN LINEAL (predicción vs. real)
    # ==========================================================
    @bp.route("/mezclas/grafico_regresion", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def grafico_regresion():
        """
        Genera los datos del gráfico de regresión lineal:
        valores reales vs. predichos del modelo entrenado.

        Body JSON esperado:
        {
            "columna": "Densidad_kg_m3"
        }
        """
        data = request.get_json(silent=True) or {}
        columna = data.get("columna")

        resultado = generar_grafico_regresion(columna=columna)
        return jsonify({
            "ok": True,
            **resultado,
        })