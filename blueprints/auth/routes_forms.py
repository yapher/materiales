"""
Rutas de formularios de autenticación:
- registro
- login
- logout
"""

from urllib.parse import urlparse

from flask import (
    render_template,
    request,
    redirect,
    url_for,
)

from utils import (
    crear_usuario,
    verificar_password,
    obtener_usuario_por_nombre,
    iniciar_sesion,
    cerrar_sesion,
)

from services.oauth_service import google_habilitado, x_habilitado


def _contexto_formularios(**extra):
    return {
        "google_habilitado": google_habilitado(),
        "x_habilitado": x_habilitado(),
        **extra,
    }


def _next_seguro(valor):
    """
    Evita redirecciones externas inseguras.
    Solo acepta rutas internas que empiecen con '/'.
    Si viene algo raro, vuelve a la página principal de mezclas.
    """
    destino_por_defecto = url_for("mezclas.index")

    if not valor:
        return destino_por_defecto

    if not isinstance(valor, str):
        return destino_por_defecto

    parsed = urlparse(valor)

    if parsed.scheme or parsed.netloc:
        return destino_por_defecto

    if not valor.startswith("/"):
        return destino_por_defecto

    return valor


def register(bp):
    """
    Registra las rutas de formularios de autenticación
    sobre el blueprint de auth.
    """

    # ==========================================================
    # REGISTRO
    # ==========================================================
    @bp.route("/registro", methods=["GET", "POST"])
    def registro():
        if request.method == "GET":
            return render_template(
                "auth/registro.html",
                **_contexto_formularios()
            )

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")
        email = request.form.get("email", "").strip() or None

        if password != password2:
            return render_template(
                "auth/registro.html",
                error="Las contraseñas no coinciden",
                **_contexto_formularios(),
            )

        if len(password) < 6:
            return render_template(
                "auth/registro.html",
                error="La contraseña debe tener al menos 6 caracteres",
                **_contexto_formularios(),
            )

        try:
            usuario = crear_usuario(username, password=password, email=email)
        except ValueError as e:
            return render_template(
                "auth/registro.html",
                error=str(e),
                **_contexto_formularios(),
            )

        iniciar_sesion(usuario)
        return redirect(url_for("mezclas.index"))

    # ==========================================================
    # LOGIN
    # ==========================================================
    @bp.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "GET":
            siguiente = _next_seguro(
                request.args.get("next")
                or request.form.get("next")
                or url_for("mezclas.index")
            )

            return render_template(
                "auth/login.html",
                next=siguiente,
                **_contexto_formularios(),
            )

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        siguiente = _next_seguro(
            request.form.get("next")
            or url_for("mezclas.index")
        )

        if not verificar_password(username, password):
            return render_template(
                "auth/login.html",
                error="Usuario o contraseña incorrectos",
                next=siguiente,
                **_contexto_formularios(),
            )

        usuario = obtener_usuario_por_nombre(username)
        iniciar_sesion(usuario)
        return redirect(siguiente)

    # ==========================================================
    # LOGOUT
    # ==========================================================
    @bp.route("/logout")
    def logout():
        cerrar_sesion()
        return redirect(url_for("home.index"))