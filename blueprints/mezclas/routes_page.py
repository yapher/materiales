"""
Rutas principales de la página de predicción.
Incluye:
- vista principal
- carga de dataset para el flujo
- estado general del usuario
"""
import logging
from flask import (
    render_template,
    jsonify,
)
from services.excel_service import (
    cargar_excel_service,
    obtener_esquema_dataset,
)
from services.mezcla_service import estado_service
from utils import (
    manejar_errores_json,
    login_required,
    login_required_json,
)

logger = logging.getLogger(__name__)


def register(bp):
    """
    Registra las rutas de página y estado general.
    """

    # ==========================================================
    # PÁGINA PRINCIPAL DE PREDICCIÓN
    # ==========================================================
    @bp.route("/mezclas")
    @login_required
    def index():
        """
        Página principal de predicción.
        El esquema de columnas se detecta dinámicamente desde
        el dataset del usuario.
        """
        try:
            esquema = obtener_esquema_dataset()
        except Exception:
            logger.exception(
                "No se pudo detectar el esquema del dataset"
            )
            esquema = {
                "elementos": [],
                "temperatura_column": None,
                "temperatura_etiqueta": "Temperatura",
                "variables_entrenables": [],
                "variables_entrenable_default": [],
            }

        return render_template(
            "index.html",
            elementos=esquema.get("elementos", []),
            temperatura_column=esquema.get("temperatura_column"),
            temperatura_etiqueta=esquema.get(
                "temperatura_etiqueta",
                "Temperatura"
            ),
            variables_entrenables=esquema.get(
                "variables_entrenables",
                []
            ),
            variables_entrenable_default=esquema.get(
                "variables_entrenable_default",
                []
            ),
        )

    # ==========================================================
    # CARGAR DATASET (usado por el flujo)
    # ==========================================================
    @bp.route("/mezclas/cargar_dataset", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def cargar_dataset():
        """
        Marca el dataset del usuario como listo y devuelve
        información básica.
        """
        info = cargar_excel_service()
        return jsonify({
            "filas": info["filas"],
            "columnas": info["columnas"],
            "mensaje": "Dataset listo",
        })

    # ==========================================================
    # ESTADO GENERAL
    # ==========================================================
    @bp.route("/mezclas/estado")
    @login_required_json
    @manejar_errores_json
    def estado():
        """
        Estado general del usuario actual:
        - dataset cargado
        - filas y columnas
        - modelo en memoria
        - modelo persistido
        - información del último entrenamiento
        """
        return jsonify(estado_service())