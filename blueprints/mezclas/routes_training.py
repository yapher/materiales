"""
Rutas de entrenamiento del modelo.
"""

from flask import (
    request,
    jsonify,
)

from services.mezcla_service import (
    iniciar_entrenamiento,
    obtener_estado_entrenamiento,
)

from utils import (
    manejar_errores_json,
    login_required_json,
)


def register(bp):
    """
    Registra las rutas de entrenamiento.
    """

    # ==========================================================
    # INICIAR ENTRENAMIENTO
    # ==========================================================
    @bp.route("/mezclas/entrenar", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def entrenar():
        """
        Inicia el entrenamiento en background.

        Body JSON esperado:

        {
            "variables": [
                "Densidad_kg_m3",
                "Viscosidad_Pa_s",
                ...
            ]
        }

        Si no se envían variables, se usa la variable por defecto
        detectada desde el dataset.
        """
        data = request.get_json(silent=True) or {}
        variables = data.get("variables")

        iniciado = iniciar_entrenamiento(targets=variables)

        if not iniciado:
            return jsonify({
                "error": (
                    "Ya hay un entrenamiento en curso "
                    "para tu usuario"
                )
            }), 409

        return jsonify({
            "ok": True,
            "mensaje": "Entrenamiento iniciado",
            "variables_solicitadas": variables,
        })

    # ==========================================================
    # ESTADO DEL ENTRENAMIENTO
    # ==========================================================
    @bp.route("/mezclas/entrenar/estado")
    @login_required_json
    @manejar_errores_json
    def entrenar_estado():
        """
        Devuelve el estado del entrenamiento en background.
        """
        return jsonify(obtener_estado_entrenamiento())