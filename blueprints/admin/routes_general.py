"""
Rutas generales del panel de administración.

Incluye:
- vista principal del panel
- estado general del sistema
- borrado del modelo entrenado
- recarga del dataset personal
- subida de un nuevo dataset maestro
"""

import os

from flask import (
    render_template,
    request,
    jsonify,
)

from services.mezcla_service import (
    estado_service,
    reset_modelo_service,
    info_modelo_service,
    obtener_estado_entrenamiento,
)

from services.excel_service import (
    recargar_dataset,
    forzar_recarga_usuario,
)

from services.dataset_upload_service import reemplazar_dataset_maestro

from utils import (
    manejar_errores_json,
    admin_required,
    admin_required_json,
)


def register(bp):
    """
    Registra las rutas generales del panel de administración
    sobre el blueprint de admin.
    """

    # ==========================================================
    # PANEL PRINCIPAL DE ADMIN
    # ==========================================================
    @bp.route("/")
    @admin_required
    def index():
        return render_template("admin/index.html")

    # ==========================================================
    # ESTADO GENERAL (dataset + modelo del usuario actual)
    # ==========================================================
    @bp.route("/estado")
    @admin_required_json
    @manejar_errores_json
    def estado():
        data = estado_service()
        data["modelo_info"] = info_modelo_service()

        return jsonify(data)

    # ==========================================================
    # BORRAR MODELO
    # ==========================================================
    @bp.route("/reset_modelo", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def reset_modelo():
        reset_modelo_service()

        return jsonify({
            "ok": True,
            "mensaje": "Modelo del usuario eliminado.",
        })

    # ==========================================================
    # RECARGAR DATASET (copia personal del admin)
    # ==========================================================
    @bp.route("/recargar_dataset", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def recargar():
        df = recargar_dataset()

        return jsonify({
            "ok": True,
            "filas": len(df),
            "columnas": len(df.columns),
            "mensaje": "Dataset recargado correctamente.",
        })

    # ==========================================================
    # SUBIR NUEVO DATASET MAESTRO
    # ==========================================================
    @bp.route("/subir_dataset", methods=["POST"])
    @admin_required_json
    @manejar_errores_json
    def subir_dataset():
        archivo = request.files.get("archivo")

        if archivo is None or not archivo.filename:
            raise ValueError("No se seleccionó ningún archivo.")

        estado = obtener_estado_entrenamiento()

        if estado.get("corriendo"):
            raise ValueError(
                "No se puede cambiar el dataset mientras hay un entrenamiento en curso."
            )

        # Reemplaza el dataset maestro, crea copias en data y deja
        # el dataset personal del usuario actual listo con el nuevo archivo.
        info = reemplazar_dataset_maestro(archivo)

        # Como cambió el dataset, el modelo entrenado ya no sirve.
        reset_modelo_service()

        # Forzar recarga del dataset personal del usuario actual en memoria.
        # Esto es clave para que "Mi dataset" muestre el nuevo.
        df = forzar_recarga_usuario()

        archivo_activo = os.path.basename(
            info.get("archivo_activo", "dataset_maestro_actual.xlsx")
        )

        mensaje = (
            "Nuevo dataset cargado correctamente. "
            f"Se está usando '{archivo_activo}' como dataset maestro. "
            "Se borró el modelo entrenado actual y tu dataset personal "
            "se recargó con el nuevo archivo."
        )

        return jsonify({
            "ok": True,
            "mensaje": mensaje,
            "filas": len(df),
            "columnas": len(df.columns),
        })