"""
Rutas de predicción.
Incluye:
- predecir
- última predicción
- guardar predicción en dataset (SOLO ADMIN)
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
    reset_modelo_service,
)
from services.pdf_service import generar_pdf_prediccion
from utils import (
    manejar_errores_json,
    login_required_json,
    admin_required_json,
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
    # GUARDAR PREDICCIÓN EN EL DATASET (SOLO ADMIN)
    # ==========================================================
    @bp.route("/mezclas/guardar_prediccion", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def guardar_prediccion():
        """
        Predice y guarda el resultado como una fila nueva en el
        dataset global. SOLO ADMIN.
        Borra el modelo entrenado.
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

        # Borrar el modelo: el dataset cambió
        reset_modelo_service()

        return jsonify({
            "ok": True,
            "mensaje": (
                f"Predicción guardada en el dataset "
                f"({resultado['filas']} filas ahora). "
                "El modelo fue eliminado. Reentrená para "
                "que la tenga en cuenta."
            ),
        })

    # ==========================================================
    # EXPORTAR PREDICCIÓN A PDF (todos)
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