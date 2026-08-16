"""
Rutas de administración del dataset maestro.

Incluye:
- vista de administración del dataset maestro
- listado de filas
- edición de filas
- borrado de filas
- agregado de filas
- exportación de una fila a PDF
"""

from flask import (
    render_template,
    request,
    jsonify,
    send_file,
)

from services.excel_service import (
    listar_filas_maestro,
    actualizar_fila_maestro,
    eliminar_fila_maestro,
    agregar_fila_maestro,
    obtener_fila_maestro,
)

from services.pdf_service import generar_pdf_fila_dataset

from utils import (
    manejar_errores_json,
    admin_required,
    admin_required_json,
)


def register(bp):
    """
    Registra las rutas del dataset maestro sobre el blueprint de admin.
    """

    # ==========================================================
    # VISTA: DATASET MAESTRO
    # ==========================================================
    @bp.route("/dataset")
    @admin_required
    def dataset():
        return render_template("admin/dataset.html")

    # ==========================================================
    # LISTAR FILAS
    # ==========================================================
    @bp.route("/dataset/filas")
    @admin_required_json
    @manejar_errores_json
    def dataset_filas():
        return jsonify(listar_filas_maestro())

    # ==========================================================
    # EDITAR FILA
    # ==========================================================
    @bp.route("/dataset/filas/<int:indice>", methods=["PUT"])
    @admin_required_json
    @manejar_errores_json
    def dataset_editar_fila(indice):
        valores = request.get_json() or {}

        actualizar_fila_maestro(indice, valores)

        return jsonify({
            "ok": True,
            "mensaje": "Fila actualizada"
        })

    # ==========================================================
    # BORRAR FILA
    # ==========================================================
    @bp.route("/dataset/filas/<int:indice>", methods=["DELETE"])
    @admin_required_json
    @manejar_errores_json
    def dataset_borrar_fila(indice):
        eliminar_fila_maestro(indice)

        return jsonify({
            "ok": True,
            "mensaje": "Fila eliminada"
        })

    # ==========================================================
    # AGREGAR FILA
    # ==========================================================
    @bp.route("/dataset/filas", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def dataset_agregar_fila():
        valores = request.get_json() or {}

        agregar_fila_maestro(valores)

        return jsonify({
            "ok": True,
            "mensaje": "Fila agregada"
        })

    # ==========================================================
    # EXPORTAR FILA A PDF
    # ==========================================================
    @bp.route("/dataset/filas/<int:indice>/pdf")
    @admin_required
    @manejar_errores_json
    def dataset_fila_pdf(indice):
        columnas, fila = obtener_fila_maestro(indice)

        buffer = generar_pdf_fila_dataset(
            "Fila del dataset maestro",
            indice,
            columnas,
            fila["valores"],
            inconsistente=fila["inconsistente"],
            motivo=fila["motivo"],
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"fila_maestro_{indice}.pdf",
        )