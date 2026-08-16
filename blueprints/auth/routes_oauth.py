"""
Rutas de login social (OAuth):
- Google
- X (Twitter)
"""

from flask import (
    redirect,
    url_for,
    flash,
)

from utils import (
    obtener_usuario_por_nombre,
    obtener_usuario_por_proveedor,
    crear_usuario,
    iniciar_sesion,
)

from services.oauth_service import (
    oauth,
    google_habilitado,
    x_habilitado,
)


def _crear_usuario_social(proveedor, proveedor_id, email=None, sugerencia=None):
    """
    Arma un nombre de usuario disponible a partir del email o del
    username de la red social, y crea la cuenta vinculada.
    """
    base = (
        sugerencia.split("@")[0]
        if sugerencia and "@" in sugerencia
        else sugerencia
    ) or f"{proveedor}_user"

    base = "".join(
        c for c in base
        if c.isalnum() or c in "_-"
    )[:20] or f"{proveedor}_user"

    if len(base) < 3:
        base = f"{base}_usr"

    username = base
    sufijo = 1

    while obtener_usuario_por_nombre(username) is not None:
        sufijo += 1
        username = f"{base}{sufijo}"

    return crear_usuario(
        username,
        email=email,
        proveedor=proveedor,
        proveedor_id=proveedor_id,
    )


def register(bp):
    """
    Registra las rutas de login social sobre el blueprint de auth.
    """

    # ==========================================================
    # LOGIN SOCIAL - GOOGLE
    # ==========================================================
    @bp.route("/login/google")
    def login_google():
        if not google_habilitado():
            flash("El login con Google todavía no está configurado en el servidor.")
            return redirect(url_for("auth.login"))

        redirect_uri = url_for("auth.callback_google", _external=True)
        return oauth.google.authorize_redirect(redirect_uri)

    @bp.route("/callback/google")
    def callback_google():
        token = oauth.google.authorize_access_token()
        perfil = token.get("userinfo") or {}

        proveedor_id = perfil.get("sub")
        email = perfil.get("email")

        usuario = obtener_usuario_por_proveedor("google", proveedor_id)

        if usuario is None:
            usuario = _crear_usuario_social(
                "google",
                proveedor_id,
                email=email,
                sugerencia=email
            )

        iniciar_sesion(usuario)
        return redirect(url_for("mezclas.index"))

    # ==========================================================
    # LOGIN SOCIAL - X
    # ==========================================================
    @bp.route("/login/x")
    def login_x():
        if not x_habilitado():
            flash("El login con X todavía no está configurado en el servidor.")
            return redirect(url_for("auth.login"))

        redirect_uri = url_for("auth.callback_x", _external=True)
        return oauth.x.authorize_redirect(redirect_uri)

    @bp.route("/callback/x")
    def callback_x():
        token = oauth.x.authorize_access_token()
        resp = oauth.x.get("users/me", token=token)
        perfil = resp.json().get("data", {})

        proveedor_id = perfil.get("id")
        nombre_x = perfil.get("username")

        usuario = obtener_usuario_por_proveedor("x", proveedor_id)

        if usuario is None:
            usuario = _crear_usuario_social(
                "x",
                proveedor_id,
                email=None,
                sugerencia=nombre_x
            )

        iniciar_sesion(usuario)
        return redirect(url_for("mezclas.index"))