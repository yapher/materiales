"""
Rutas principales del perfil de usuario:
- Vista del perfil (datos personales + contraseña + avatar)
- Actualización de datos personales (email, nombre)
"""
from flask import (
    render_template,
    request,
    jsonify,
)
from services.perfil import actualizar_datos_service
from utils import (
    manejar_errores_json,
    login_required,
    login_required_json,
    usuario_actual,
)


def register(bp):
    """
    Registra las rutas del perfil sobre el blueprint.
    """

    # ==========================================================
    # VISTA PRINCIPAL DEL PERFIL
    # ==========================================================
    @bp.route("/")
    @login_required
    def index():
        """
        Página de perfil del usuario actual.
        Muestra tres secciones:
        1. Foto de perfil
        2. Datos personales
        3. Cambio de contraseña
        """
        usuario = usuario_actual()
        return render_template(
            "perfil/index.html",
            usuario=usuario,
        )

    # ==========================================================
    # ACTUALIZAR DATOS PERSONALES
    # ==========================================================
    @bp.route("/actualizar_datos", methods=["POST"])
    @login_required_json
    @manejar_errores_json
    def actualizar_datos():
        """
        Actualiza email y nombre del usuario actual.
        Body JSON esperado:
        {
            "email": "user@example.com",
            "nombre": "Juan Pérez"
        }
        """
        data = request.get_json(silent=True) or {}
        email = data.get("email", "").strip() or None
        nombre = data.get("nombre", "").strip() or None

        resultado = actualizar_datos_service(
            email=email,
            nombre=nombre,
        )
        return jsonify({
            "ok": True,
            "mensaje": "Datos personales actualizados correctamente.",
            "datos": resultado,
        })