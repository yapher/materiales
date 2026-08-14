"""
Registro de proveedores de login social (Google, X) usando Authlib.

Cada proveedor se registra SOLO si estan definidas sus credenciales
(Config.GOOGLE_CLIENT_ID/SECRET, Config.X_CLIENT_ID/SECRET). Si faltan,
el proveedor queda deshabilitado: el boton correspondiente no se
muestra y las rutas /auth/login/<proveedor> redirigen con un aviso, en
vez de romper la app.
"""
import logging

from authlib.integrations.flask_client import OAuth

from config import Config

logger = logging.getLogger(__name__)

oauth = OAuth()


def init_oauth(app):
    oauth.init_app(app)

    if google_habilitado():
        oauth.register(
            name="google",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
        logger.info("Login con Google habilitado")
    else:
        logger.info("Login con Google deshabilitado (faltan GOOGLE_CLIENT_ID/SECRET)")

    if x_habilitado():
        oauth.register(
            name="x",
            client_id=Config.X_CLIENT_ID,
            client_secret=Config.X_CLIENT_SECRET,
            access_token_url="https://api.twitter.com/2/oauth2/token",
            authorize_url="https://twitter.com/i/oauth2/authorize",
            api_base_url="https://api.twitter.com/2/",
            client_kwargs={
                "scope": "tweet.read users.read offline.access",
                "code_challenge_method": "S256",
            },
        )
        logger.info("Login con X habilitado")
    else:
        logger.info("Login con X deshabilitado (faltan X_CLIENT_ID/SECRET)")


def google_habilitado():
    return bool(Config.GOOGLE_CLIENT_ID and Config.GOOGLE_CLIENT_SECRET)


def x_habilitado():
    return bool(Config.X_CLIENT_ID and Config.X_CLIENT_SECRET)
