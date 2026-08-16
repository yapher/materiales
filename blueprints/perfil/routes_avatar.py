"""
Rutas de gestión de foto de perfil (avatar):
- Servir el avatar actual (GET)
- Subir un nuevo avatar (POST)
- Eliminar el avatar (DELETE)
"""
import os
from flask import (
    request,
    jsonify,
    send_file,
    abort,
)
from services.perfil import (
    guardar_avatar_service,
    eliminar_avatar_service,
    obtener_ruta_avatar,
)
from utils import (
    manejar_errores_json,
    login_required,
    login_required_json,
)


def register(bp):
    """
    Registra las rutas de avatar sobre el blueprint de perfil.
    """

    # ==========================================================
    # SERVIR AVATAR (GET)
    # ==========================================================
    @bp.route("/avatar")
    @login_required
    def avatar():
        """
        Sirve la foto de perfil del usuario actual.
        Se usa en el navbar y en la página de perfil.
        Si no tiene avatar, devuelve 404.
        """
        ruta = obtener_ruta_avatar()
        if ruta is None or not os.path.exists(ruta):
            abort(404)
        return send_file(ruta)

    # ==========================================================
    # SUBIR AVATAR (POST)
    # ==========================================================
    @bp.route("/avatar", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def subir_avatar():
        """
        Sube una nueva foto de perfil.
        Espera un multipart/form-data con campo 'avatar'.
        """
        archivo = request.files.get("avatar")
        if archivo is None or not archivo.filename:
            raise ValueError("No se seleccionó ningún archivo.")

        guardar_avatar_service(archivo)
        return jsonify({
            "ok": True,
            "mensaje": "Foto de perfil actualizada correctamente.",
        })

    # ==========================================================
    # ELIMINAR AVATAR (DELETE)
    # ==========================================================
    @bp.route("/avatar", methods=["DELETE"])
    @login_required_json
    @manejar_errores_json
    def eliminar_avatar():
        """
        Elimina la foto de perfil del usuario actual.
        """
        eliminar_avatar_service()
        return jsonify({
            "ok": True,
            "mensaje": "Foto de perfil eliminada.",
        })