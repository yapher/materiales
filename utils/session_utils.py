import os
import shutil
from datetime import datetime

from flask import session

from config import Config


def obtener_user_id():
    """
    Devuelve el identificador del usuario ACTUAL, que ahora es su nombre
    de usuario real (no un uuid anonimo como en la version anterior).

    Requiere que haya una sesion iniciada (session["username"]). Las
    rutas que llegan hasta acá siempre están protegidas con
    @login_required / @admin_required (ver utils/auth.py), así que en
    la práctica esto nunca deberia dispararse sin sesion. Si pasara
    igual, es mejor un error explícito que crear datos "fantasma".
    """
    username = session.get("username")

    if username is None:
        raise RuntimeError(
            "obtener_user_id() llamado sin sesión iniciada. "
            "La ruta que llegó hasta acá debería estar protegida con "
            "@login_required o @admin_required."
        )

    return username


def carpeta_usuario(user_id=None):
    """
    Carpeta en disco exclusiva del usuario (data/users/<username>/).

    Acepta un user_id explícito (usado por el entrenamiento en
    background, que corre en un hilo SIN contexto de sesión/request) o,
    si no se pasa nada, lo resuelve de la sesión actual como antes.
    """
    user_id = user_id or obtener_user_id()

    ruta = os.path.join(Config.USERS_DIR, user_id)
    os.makedirs(ruta, exist_ok=True)

    return ruta


def archivo_dataset_usuario(user_id=None):
    return os.path.join(carpeta_usuario(user_id), "dataset.xlsx")


def archivo_modelo_usuario(user_id=None):
    return os.path.join(carpeta_usuario(user_id), "modelo.pkl")


def archivo_info_usuario(user_id=None):
    return os.path.join(carpeta_usuario(user_id), "info_modelo.json")


def archivo_ultima_prediccion_usuario(user_id=None):
    return os.path.join(carpeta_usuario(user_id), "ultima_prediccion.json")


def eliminar_carpeta_usuario(username):
    """
    Elimina la carpeta de datos de un usuario (dataset, modelo, etc.)
    """
    ruta = os.path.join(Config.USERS_DIR, username)
    
    if os.path.exists(ruta):
        shutil.rmtree(ruta)
        return True
    return False


def limpiar_usuario(user_id):
    """
    Borra la carpeta de un usuario si lleva más de 30 días sin actividad
    (se mide por la fecha de modificación de la carpeta).
    """
    ruta = os.path.join(Config.USERS_DIR, user_id)

    if os.path.exists(ruta):
        fecha = os.path.getmtime(ruta)
        dias = (datetime.now().timestamp() - fecha) / 86400

        if dias > 30:
            import shutil
            shutil.rmtree(ruta)