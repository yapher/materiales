"""
Rutas del dataset global.
Incluye:
- vista del dataset (todos los usuarios logueados)
- listado de filas (todos)
- editar fila (SOLO ADMIN)
- borrar fila (SOLO ADMIN)
- agregar fila (SOLO ADMIN)
- exportar fila a PDF (todos)

IMPORTANTE:
- Si el admin edita/borra/agrega, se borra el modelo entrenado.
- Los usuarios no-admin solo pueden ver y exportar a PDF.
"""
from flask import (
    render_template,
    request,
    jsonify,
    send_file,
)
from services.excel_service import (
    listar_filas_maestro,
    eliminar_fila_maestro,
    obtener_fila_maestro,
    actualizar_fila_maestro,
    agregar_fila_maestro,
)
from services.mezcla_service import reset_modelo_service
from services.pdf_service import generar_pdf_fila_dataset
from utils import (
    manejar_errores_json,
    login_required,
    login_required_json,
    admin_required_json,
    usuario_actual,
)


def register(bp):
    """
    Registra las rutas del dataset global.
    """

    # ==========================================================
    # VISTA: DATASET (todos los usuarios)
    # ==========================================================
    @bp.route("/mezclas/dataset")
    @login_required
    def dataset_view():
        """
        Página donde se ve el dataset global.
        El admin puede editar; los demás solo ver y exportar.
        """
        usuario = usuario_actual()
        es_admin = usuario.get("es_admin", False) if usuario else False
        return render_template(
            "dataset.html",
            es_admin=es_admin,
        )

    # ==========================================================
    # LISTAR FILAS (todos los usuarios logueados)
    # ==========================================================
    @bp.route("/mezclas/dataset/filas")
    @login_required_json
    @manejar_errores_json
    def dataset_filas():
        """
        Devuelve columnas y filas del dataset global.
        """
        usuario = usuario_actual()
        es_admin = usuario.get("es_admin", False) if usuario else False
        data = listar_filas_maestro()
        data["es_admin"] = es_admin
        return jsonify(data)

    # ==========================================================
    # EDITAR FILA (SOLO ADMIN)
    # ==========================================================
    @bp.route(
        "/mezclas/dataset/filas/<int:indice>",
        methods=["PUT"]
    )
    @admin_required_json
    @manejar_errores_json
    def dataset_editar_fila(indice):
        """
        Actualiza una fila del dataset global.
        Borra el modelo entrenado del admin.
        """
        valores = request.get_json(silent=True) or {}
        actualizar_fila_maestro(indice, valores)

        # Borrar el modelo: el dataset cambió
        reset_modelo_service()

        return jsonify({
            "ok": True,
            "mensaje": (
                "Fila actualizada. El modelo fue eliminado, "
                "reentrená para generar uno nuevo."
            ),
        })

    # ==========================================================
    # BORRAR FILA (SOLO ADMIN)
    # ==========================================================
    @bp.route(
        "/mezclas/dataset/filas/<int:indice>",
        methods=["DELETE"]
    )
    @admin_required_json
    @manejar_errores_json
    def dataset_borrar_fila(indice):
        """
        Elimina una fila del dataset global.
        Borra el modelo entrenado del admin.
        """
        eliminar_fila_maestro(indice)

        # Borrar el modelo: el dataset cambió
        reset_modelo_service()

        return jsonify({
            "ok": True,
            "mensaje": (
                "Fila eliminada del dataset. El modelo fue eliminado, "
                "reentrená para generar uno nuevo."
            ),
        })

    # ==========================================================
    # AGREGAR FILA (SOLO ADMIN)
    # ==========================================================
    @bp.route("/mezclas/dataset/filas", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def dataset_agregar_fila():
        """
        Agrega una fila al dataset global.
        Borra el modelo entrenado del admin.
        """
        valores = request.get_json(silent=True) or {}
        agregar_fila_maestro(valores)

        # Borrar el modelo: el dataset cambió
        reset_modelo_service()

        return jsonify({
            "ok": True,
            "mensaje": (
                "Fila agregada. El modelo fue eliminado, "
                "reentrená para generar uno nuevo."
            ),
        })

    # ==========================================================
    # EXPORTAR FILA A PDF (todos los usuarios)
    # ==========================================================
    @bp.route("/mezclas/dataset/filas/<int:indice>/pdf")
    @login_required
    @manejar_errores_json
    def dataset_fila_pdf(indice):
        """
        Genera un PDF con una fila del dataset global.
        Disponible para todos los usuarios.
        """
        columnas, fila = obtener_fila_maestro(indice)
        usuario = usuario_actual()
        buffer = generar_pdf_fila_dataset(
            "Fila del dataset",
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