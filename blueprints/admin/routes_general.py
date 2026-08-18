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
    # BORRAR MODELO (solo el del admin actual)
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
                "No se puede cambiar el dataset mientras hay "
                "un entrenamiento en curso."
            )

        # Reemplaza el dataset maestro y propaga a todos los usuarios.
        info = reemplazar_dataset_maestro(archivo)

        # Nota: reset_modelo_service() ya no es estrictamente necesario
        # porque reemplazar_dataset_maestro() ahora borra los modelos
        # de TODOS los usuarios (incluido el admin). Se mantiene por
        # seguridad (limpia también el estado de entrenamiento del admin).
        reset_modelo_service()

        # Forzar recarga del dataset personal del admin en memoria.
        df = forzar_recarga_usuario()

        archivo_activo = os.path.basename(
            info.get("archivo_activo", "dataset_maestro_actual.xlsx")
        )
        usuarios_actualizados = info.get("usuarios_actualizados", 0)
        modelos_borrados = info.get("modelos_borrados", 0)

        mensaje = (
            "Nuevo dataset cargado correctamente. "
            f"Se está usando '{archivo_activo}' como dataset maestro. "
            f"Se actualizaron los datasets de {usuarios_actualizados} "
            f"usuario(s) y se borraron {modelos_borrados} modelo(s) "
            f"entrenado(s). Todos los usuarios deberán reentrenar "
            f"su modelo la próxima vez que entren."
        )

        return jsonify({
            "ok": True,
            "mensaje": mensaje,
            "filas": len(df),
            "columnas": len(df.columns),
            "usuarios_actualizados": usuarios_actualizados,
            "modelos_borrados": modelos_borrados,
        })