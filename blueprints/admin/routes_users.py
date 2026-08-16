"""
Rutas de administración de usuarios.

Incluye:
- vista de administración de usuarios
- listado de usuarios
- cambio de rol (admin / usuario común)
- eliminación de usuarios
"""

from flask import (
    render_template,
    request,
    jsonify,
)

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


def register(bp):
    """
    Registra las rutas de administración de usuarios
    sobre el blueprint de admin.
    """

    # ==========================================================
    # VISTA: USUARIOS
    # ==========================================================
    @bp.route("/usuarios")
    @admin_required
    def usuarios():
        return render_template("admin/usuarios.html")

    # ==========================================================
    # LISTAR USUARIOS
    # ==========================================================
    @bp.route("/usuarios/lista")
    @admin_required_json
    @manejar_errores_json
    def usuarios_lista():
        return jsonify({
            "usuarios": listar_usuarios(),
            "usuario_actual": usuario_actual()["username"],
        })

    # ==========================================================
    # CAMBIAR ROL
    # ==========================================================
    @bp.route("/usuarios/<username>/rol", methods=["POST"])
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

    # ==========================================================
    # ELIMINAR USUARIO
    # ==========================================================
    @bp.route("/usuarios/<username>", methods=["DELETE"])
    @admin_required_json
    @manejar_errores_json
    def usuarios_eliminar(username):
        """
        Elimina un usuario completamente:

        1. Lo borra de la base de usuarios.
        2. Elimina su carpeta de datos (dataset, modelo, etc.).
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