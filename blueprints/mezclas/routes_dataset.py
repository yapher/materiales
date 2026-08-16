"""
Rutas del dataset personal del usuario.

Incluye:
- vista de mi dataset
- listado de filas
- editar fila
- borrar fila
- exportar fila a PDF
"""

from flask import (
    render_template,
    request,
    jsonify,
    send_file,
)

from services.excel_service import (
    listar_filas_usuario,
    eliminar_fila_usuario,
    obtener_fila_usuario,
    actualizar_fila_usuario,
)

from services.pdf_service import generar_pdf_fila_dataset

from utils import (
    manejar_errores_json,
    login_required,
    login_required_json,
    usuario_actual,
)


def register(bp):
    """
    Registra las rutas del dataset personal.
    """

    # ==========================================================
    # VISTA: MI DATASET
    # ==========================================================
    @bp.route("/mezclas/dataset")
    @login_required
    def dataset_view():
        """
        Página donde el usuario ve su dataset personal.
        """
        return render_template("mi_dataset.html")

    # ==========================================================
    # LISTAR FILAS
    # ==========================================================
    @bp.route("/mezclas/dataset/filas")
    @login_required_json
    @manejar_errores_json
    def dataset_filas():
        """
        Devuelve columnas y filas del dataset personal.
        """
        return jsonify(listar_filas_usuario())

    # ==========================================================
    # EDITAR FILA
    # ==========================================================
    @bp.route(
        "/mezclas/dataset/filas/<int:indice>",
        methods=["PUT"]
    )
    @login_required_json
    @manejar_errores_json
    def dataset_editar_fila(indice):
        """
        Actualiza una fila del dataset personal.
        """
        valores = request.get_json(silent=True) or {}

        actualizar_fila_usuario(
            indice,
            valores
        )

        return jsonify({
            "ok": True,
            "mensaje": "Fila actualizada"
        })

    # ==========================================================
    # BORRAR FILA
    # ==========================================================
    @bp.route(
        "/mezclas/dataset/filas/<int:indice>",
        methods=["DELETE"]
    )
    @login_required_json
    @manejar_errores_json
    def dataset_borrar_fila(indice):
        """
        Elimina una fila del dataset personal.
        """
        eliminar_fila_usuario(indice)

        return jsonify({
            "ok": True,
            "mensaje": (
                "Fila eliminada de tu dataset. "
                "Reentrená el modelo si ya lo habías "
                "entrenado con ella."
            ),
        })

    # ==========================================================
    # EXPORTAR FILA A PDF
    # ==========================================================
    @bp.route("/mezclas/dataset/filas/<int:indice>/pdf")
    @login_required
    @manejar_errores_json
    def dataset_fila_pdf(indice):
        """
        Genera un PDF con una fila del dataset personal.
        """
        columnas, fila = obtener_fila_usuario(indice)

        usuario = usuario_actual()

        buffer = generar_pdf_fila_dataset(
            "Fila de mi dataset",
            indice,
            columnas,
            fila["valores"],
            inconsistente=fila["inconsistente"],
            motivo=fila["motivo"],
            generado_para=usuario["username"] if usuario else None,
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"fila_dataset_{indice}.pdf",
        )