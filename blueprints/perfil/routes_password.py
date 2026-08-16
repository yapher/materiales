"""
Rutas de cambio de contraseña del perfil de usuario.
"""
from flask import (
    request,
    jsonify,
)
from services.perfil import cambiar_password_service
from utils import (
    manejar_errores_json,
    login_required_json,
)


def register(bp):
    """
    Registra las rutas de cambio de contraseña
    sobre el blueprint de perfil.
    """

    # ==========================================================
    # CAMBIAR CONTRASEÑA
    # ==========================================================
    @bp.route("/cambiar_password", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def cambiar_password():
        """
        Cambia la contraseña del usuario actual.
        Body JSON esperado:
        {
            "password_actual": "clave_vieja",
            "password_nueva": "clave_nueva",
            "password_nueva2": "clave_nueva"
        }
        """
        data = request.get_json(silent=True) or {}
        password_actual = data.get("password_actual", "")
        password_nueva = data.get("password_nueva", "")
        password_nueva2 = data.get("password_nueva2", "")

        cambiar_password_service(
            password_actual,
            password_nueva,
            password_nueva2,
        )
        return jsonify({
            "ok": True,
            "mensaje": "Contraseña actualizada correctamente.",
        })