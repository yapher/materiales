import os

from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_file,
)

from services.mezcla_service import (
    estado_service,
    reset_modelo_service,
    info_modelo_service,
    obtener_estado_entrenamiento,
)

from services.excel_service import (
    recargar_dataset,
    listar_filas_maestro,
    actualizar_fila_maestro,
    eliminar_fila_maestro,
    agregar_fila_maestro,
    obtener_fila_maestro,
    forzar_recarga_usuario,
)

from services.dataset_upload_service import reemplazar_dataset_maestro

from services.pdf_service import generar_pdf_fila_dataset

from utils import (
    manejar_errores_json,
    admin_required,
    admin_required_json,
    listar_usuarios,
    hacer_admin,
    eliminar_usuario,
    eliminar_carpeta_usuario,
    usuario_actual,
)

admin_bp = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
    url_prefix="/admin",
)


@admin_bp.route("/")
@admin_required
def index():
    return render_template("admin/index.html")


# ==========================================================
# ESTADO GENERAL (dataset + modelo del usuario actual)
# ==========================================================
@admin_bp.route("/estado")
@admin_required_json
@manejar_errores_json
def estado():
    data = estado_service()
    data["modelo_info"] = info_modelo_service()

    return jsonify(data)


# ==========================================================
# BORRAR MODELO
# ==========================================================
@admin_bp.route("/reset_modelo", methods=["POST"])
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
@admin_bp.route("/recargar_dataset", methods=["POST"])
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
@admin_bp.route("/subir_dataset", methods=["POST"])
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


# ==========================================================
# DATASET MAESTRO: ver / editar / borrar / agregar filas
# ==========================================================
@admin_bp.route("/dataset")
@admin_required
def dataset():
    return render_template("admin/dataset.html")


@admin_bp.route("/dataset/filas")
@admin_required_json
@manejar_errores_json
def dataset_filas():
    return jsonify(listar_filas_maestro())


@admin_bp.route("/dataset/filas/<int:indice>", methods=["PUT"])
@admin_required_json
@manejar_errores_json
def dataset_editar_fila(indice):
    valores = request.get_json() or {}

    actualizar_fila_maestro(indice, valores)

    return jsonify({"ok": True, "mensaje": "Fila actualizada"})


@admin_bp.route("/dataset/filas/<int:indice>", methods=["DELETE"])
@admin_required_json
@manejar_errores_json
def dataset_borrar_fila(indice):
    eliminar_fila_maestro(indice)

    return jsonify({"ok": True, "mensaje": "Fila eliminada"})


@admin_bp.route("/dataset/filas", methods=["POST"])
@admin_required_json
@manejar_errores_json
def dataset_agregar_fila():
    valores = request.get_json() or {}

    agregar_fila_maestro(valores)

    return jsonify({"ok": True, "mensaje": "Fila agregada"})


@admin_bp.route("/dataset/filas/<int:indice>/pdf")
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


# ==========================================================
# USUARIOS: listar, otorgar/quitar privilegios y eliminar
# ==========================================================
@admin_bp.route("/usuarios")
@admin_required
def usuarios():
    return render_template("admin/usuarios.html")


@admin_bp.route("/usuarios/lista")
@admin_required_json
@manejar_errores_json
def usuarios_lista():
    return jsonify({
        "usuarios": listar_usuarios(),
        "usuario_actual": usuario_actual()["username"],
    })


@admin_bp.route("/usuarios/<username>/rol", methods=["POST"])
@admin_required_json
@manejar_errores_json
def usuarios_cambiar_rol(username):
    data = request.get_json() or {}

    es_admin = bool(data.get("es_admin"))

    yo = usuario_actual()

    if yo["username"].lower() == username.lower() and not es_admin:
        raise ValueError(
            "No podés quitarte tus propios permisos de administrador"
        )

    hacer_admin(username, es_admin)

    return jsonify({
        "ok": True,
        "mensaje": (
            f"{username} ahora es "
            f"{'administrador' if es_admin else 'usuario común'}."
        ),
    })


@admin_bp.route("/usuarios/<username>", methods=["DELETE"])
@admin_required_json
@manejar_errores_json
def usuarios_eliminar(username):
    """
    Elimina un usuario completamente:
    1. Lo borra de la base de usuarios
    2. Elimina su carpeta de datos (dataset, modelo, etc.)
    """
    yo = usuario_actual()

    # No permitir que un admin se elimine a sí mismo.
    if yo["username"].lower() == username.lower():
        raise ValueError(
            "No podés eliminarte a ti mismo. "
            "Usá la opción 'Darme de baja' en tu perfil."
        )

    # No permitir eliminar al admin semilla.
    if username.lower() == "jazmin":
        raise ValueError(
            "No se puede eliminar al usuario administrador principal"
        )

    # Eliminar usuario de la base de datos.
    eliminar_usuario(username)

    # Eliminar carpeta de datos del usuario.
    eliminar_carpeta_usuario(username)

    return jsonify({
        "ok": True,
        "mensaje": (
            f"Usuario '{username}' eliminado correctamente "
            f"junto con todos sus datos."
        ),
    })