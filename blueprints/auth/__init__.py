from urllib.parse import urlparse

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)

from utils import (
    crear_usuario,
    verificar_password,
    obtener_usuario_por_nombre,
    obtener_usuario_por_proveedor,
    iniciar_sesion,
    cerrar_sesion,
)

from services.oauth_service import oauth, google_habilitado, x_habilitado


auth_bp = Blueprint(
    "auth",
    __name__,
    template_folder="templates",
    url_prefix="/auth",
)


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

    # Si tiene scheme o netloc, es una URL externa.
    if parsed.scheme or parsed.netloc:
        return destino_por_defecto

    # Solo aceptar rutas internas.
    if not valor.startswith("/"):
        return destino_por_defecto

    return valor


# ==========================================================
# REGISTRO
# ==========================================================
@auth_bp.route("/registro", methods=["GET", "POST"])
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
# LOGIN / LOGOUT
# ==========================================================
@auth_bp.route("/login", methods=["GET", "POST"])
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


@auth_bp.route("/logout")
def logout():
    cerrar_sesion()
    return redirect(url_for("home.index"))


# ==========================================================
# LOGIN SOCIAL - GOOGLE
# ==========================================================
@auth_bp.route("/login/google")
def login_google():
    if not google_habilitado():
        flash("El login con Google todavía no está configurado en el servidor.")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.callback_google", _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route("/callback/google")
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
@auth_bp.route("/login/x")
def login_x():
    if not x_habilitado():
        flash("El login con X todavía no está configurado en el servidor.")
        return redirect(url_for("auth.login"))

    redirect_uri = url_for("auth.callback_x", _external=True)
    return oauth.x.authorize_redirect(redirect_uri)


@auth_bp.route("/callback/x")
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


# ==========================================================
# HELPER: crear cuenta a partir de un login social
# ==========================================================
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