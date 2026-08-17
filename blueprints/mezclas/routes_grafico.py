"""
Rutas para la generación de gráficos a partir del modelo entrenado.
Actualmente incluye:
- Gráfico de densidad vs. temperatura (evolución térmica)
"""
import logging
from flask import (
    request,
    jsonify,
)
from services.mezcla_service import (
    generar_grafico_densidad,
)
from utils import (
    manejar_errores_json,
    login_required_json,
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
            "mix": [
                {"elemento": "CaO", "pct": 40},
                {"elemento": "SiO2", "pct": 60}
            ],
            "temp_min": 1500,
            "temp_max": 2000,
            "intervalo": 20
        }

        Devuelve:
        {
            "ok": true,
            "columna": "Densidad_kg_m3",
            "etiqueta": "Densidad (kg/m³)",
            "unidad_y": "kg/m³",
            "unidad_x": "K",
            "puntos": [
                {"temperatura": 1500, "densidad": 2800.12},
                ...
            ],
            "stats": {
                "min": 2750.0,
                "max": 3100.0,
                "promedio": 2920.0,
                "cantidad": 26
            }
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