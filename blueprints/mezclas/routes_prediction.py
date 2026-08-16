"""
Rutas de predicción.

Incluye:
- predecir
- última predicción
- guardar predicción en dataset
- exportar predicción a PDF
"""

from flask import (
    request,
    jsonify,
    send_file,
)

from services.excel_service import guardar_prediccion_en_dataset

from services.mezcla_service import (
    predecir_service,
    guardar_ultima_prediccion,
    obtener_ultima_prediccion,
)

from services.pdf_service import generar_pdf_prediccion

from utils import (
    manejar_errores_json,
    login_required_json,
    usuario_actual,
)


def register(bp):
    """
    Registra las rutas de predicción.
    """

    # ==========================================================
    # PREDECIR
    # ==========================================================
    @bp.route("/mezclas/predecir", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def predecir():
        """
        Predice propiedades para una mezcla y temperatura.

        Body JSON esperado:

        {
            "mix": [
                {"elemento": "CaO", "pct": 40},
                {"elemento": "SiO2", "pct": 60}
            ],
            "temperatura": 1673
        }
        """
        data = request.get_json(silent=True) or {}

        mix = data.get("mix", [])
        temperatura = data.get("temperatura")

        resultado = predecir_service(
            mix,
            temperatura
        )

        guardar_ultima_prediccion(
            mix,
            temperatura,
            resultado
        )

        return jsonify({
            "tabla_prediccion": resultado
        })

    # ==========================================================
    # ÚLTIMA PREDICCIÓN
    # ==========================================================
    @bp.route("/mezclas/ultima_prediccion")
    @login_required_json
    @manejar_errores_json
    def ultima_prediccion():
        """
        Devuelve la última predicción guardada para el usuario.
        """
        datos = obtener_ultima_prediccion()

        return jsonify(datos or {})

    # ==========================================================
    # GUARDAR PREDICCIÓN EN EL DATASET PERSONAL
    # ==========================================================
    @bp.route("/mezclas/guardar_prediccion", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def guardar_prediccion():
        """
        Predice y guarda el resultado como una fila nueva en el
        dataset personal del usuario.
        """
        data = request.get_json(silent=True) or {}

        mix = data.get("mix", [])
        temperatura = data.get("temperatura")

        tabla = predecir_service(
            mix,
            temperatura
        )

        resultado = guardar_prediccion_en_dataset(
            mix,
            temperatura,
            tabla
        )

        return jsonify({
            "ok": True,
            "mensaje": (
                f"Predicción guardada en tu dataset "
                f"({resultado['filas']} filas ahora). "
                "Reentrená el modelo para que la tenga en cuenta."
            ),
        })

    # ==========================================================
    # EXPORTAR PREDICCIÓN A PDF
    # ==========================================================
    @bp.route("/mezclas/predecir/pdf", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def predecir_pdf():
        """
        Genera un PDF con la predicción para la mezcla enviada.
        """
        data = request.get_json(silent=True) or {}

        mix = data.get("mix", [])
        temperatura = data.get("temperatura")

        tabla = predecir_service(
            mix,
            temperatura
        )

        usuario = usuario_actual()

        buffer = generar_pdf_prediccion(
            mix,
            temperatura,
            tabla,
            usuario=usuario["username"] if usuario else None,
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="prediccion_mezcla.pdf",
        )