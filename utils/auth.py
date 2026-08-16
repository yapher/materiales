"""
Manejo de cuentas de usuario: registro, login, roles (admin/usuario) y
login social (Google/X). La "base de datos" es un JSON simple en
Config.USUARIOS_DB - alcanza para esta escala; si el proyecto crece
mucho, este archivo es el unico lugar que habria que migrar a una base
de datos real.
"""
import os
import json
import re
import threading
import logging
from functools import wraps
from flask import session, redirect, url_for, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config

logger = logging.getLogger(__name__)

_lock_usuarios = threading.Lock()

# Usuario valido: letras, numeros, guion y guion bajo, 3 a 30 caracteres.
# Se usa tal cual como nombre de carpeta en disco (data/users/<usuario>),
# por eso es importante restringirlo.
_PATRON_USUARIO = re.compile(r"^[a-zA-Z0-9_-]{3,30}$")


# ==========================================================
# LECTURA / ESCRITURA DE LA BASE DE USUARIOS
# ==========================================================

def _cargar_usuarios():
    if not os.path.exists(Config.USUARIOS_DB):
        return {}
    with open(Config.USUARIOS_DB, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_usuarios(usuarios):
    os.makedirs(os.path.dirname(Config.USUARIOS_DB), exist_ok=True)
    # Escritura atomica: primero a un archivo temporal y despues rename,
    # para no dejar el JSON a medio escribir si el proceso se corta.
    tmp = Config.USUARIOS_DB + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=2)
    os.replace(tmp, Config.USUARIOS_DB)


def obtener_usuario_por_nombre(username):
    usuarios = _cargar_usuarios()
    return usuarios.get(username.lower())


def obtener_usuario_por_proveedor(proveedor, proveedor_id):
    """Busca un usuario vinculado a una cuenta de login social."""
    usuarios = _cargar_usuarios()
    for u in usuarios.values():
        if u.get("proveedor") == proveedor and u.get("proveedor_id") == proveedor_id:
            return u
    return None


def validar_username(username):
    if not username or not _PATRON_USUARIO.match(username):
        return False, "El usuario debe tener 3-30 caracteres: letras, numeros, - o _"
    return True, None


def crear_usuario(username, password=None, email=None, es_admin=False,
                  proveedor=None, proveedor_id=None, nombre=None):
    """
    Crea un usuario nuevo. Para cuentas usuario/contraseña, pasa
    'password'. Para cuentas de login social, pasa 'proveedor' y
    'proveedor_id' (y password=None).
    Lanza ValueError si el usuario ya existe o es invalido.
    """
    valido, error = validar_username(username)
    if not valido:
        raise ValueError(error)

    clave = username.lower()
    with _lock_usuarios:
        usuarios = _cargar_usuarios()
        if clave in usuarios:
            raise ValueError("Ese nombre de usuario ya está en uso")

        usuarios[clave] = {
            "username": username,
            "email": email,
            "nombre": nombre,
            "password_hash": generate_password_hash(password) if password else None,
            "es_admin": es_admin,
            "proveedor": proveedor,       # None, "google" o "x"
            "proveedor_id": proveedor_id,
        }
        _guardar_usuarios(usuarios)

    logger.info("Usuario creado: %s (admin=%s, proveedor=%s)", username, es_admin, proveedor)
    return usuarios[clave]


def verificar_password(username, password):
    usuario = obtener_usuario_por_nombre(username)
    if usuario is None or usuario.get("password_hash") is None:
        return False
    return check_password_hash(usuario["password_hash"], password)


def cambiar_password(username, nueva_password):
    """
    Cambia la contraseña de un usuario.
    Genera un nuevo hash y lo guarda en la base de usuarios.
    """
    with _lock_usuarios:
        usuarios = _cargar_usuarios()
        clave = username.lower()
        if clave not in usuarios:
            raise ValueError("Usuario inexistente")
        usuarios[clave]["password_hash"] = generate_password_hash(nueva_password)
        _guardar_usuarios(usuarios)
    logger.info("Contraseña actualizada para usuario %s", username)


def actualizar_perfil(username, email=None, nombre=None):
    """
    Actualiza los datos personales de un usuario.
    Campos editables: email, nombre.
    Si se pasa None, el campo se limpia (se setea a None).
    """
    with _lock_usuarios:
        usuarios = _cargar_usuarios()
        clave = username.lower()
        if clave not in usuarios:
            raise ValueError("Usuario inexistente")
        usuarios[clave]["email"] = email if email else None
        usuarios[clave]["nombre"] = nombre if nombre else None
        _guardar_usuarios(usuarios)
    logger.info("Perfil actualizado para usuario %s", username)


def hacer_admin(username, es_admin=True):
    with _lock_usuarios:
        usuarios = _cargar_usuarios()
        clave = username.lower()
        if clave not in usuarios:
            raise ValueError("Usuario inexistente")
        usuarios[clave]["es_admin"] = es_admin
        _guardar_usuarios(usuarios)
    logger.info("Usuario %s -> es_admin=%s", username, es_admin)


def eliminar_usuario(username):
    """
    Elimina un usuario de la base de datos.
    Lanza ValueError si el usuario no existe.
    """
    with _lock_usuarios:
        usuarios = _cargar_usuarios()
        clave = username.lower()
        if clave not in usuarios:
            raise ValueError("Usuario inexistente")
        # No permitir eliminar al usuario administrador semilla
        if clave == Config.ADMIN_SEED_USUARIO.lower():
            raise ValueError("No se puede eliminar al usuario administrador principal")
        del usuarios[clave]
        _guardar_usuarios(usuarios)
    logger.info("Usuario eliminado: %s", username)


def listar_usuarios():
    """Devuelve la lista de usuarios SIN el hash de contraseña, para mostrar en Admin."""
    usuarios = _cargar_usuarios()
    return [
        {
            "username": u["username"],
            "email": u.get("email"),
            "nombre": u.get("nombre"),
            "es_admin": u.get("es_admin", False),
            "proveedor": u.get("proveedor"),
        }
        for u in usuarios.values()
    ]


def asegurar_admin_semilla():
    """
    Crea el usuario administrador inicial (Config.ADMIN_SEED_USUARIO) si
    todavia no existe ningun usuario con ese nombre. Se llama una vez al
    arrancar el servidor (no depende de sesion/request, así que es
    seguro llamarlo desde app.py).
    """
    if obtener_usuario_por_nombre(Config.ADMIN_SEED_USUARIO) is not None:
        return
    crear_usuario(
        Config.ADMIN_SEED_USUARIO,
        password=Config.ADMIN_SEED_PASSWORD,
        es_admin=True,
    )
    logger.info(
        "Usuario administrador semilla creado: %s (cambiá la contraseña "
        "despues del primer login si esto va a produccion)",
        Config.ADMIN_SEED_USUARIO,
    )


# ==========================================================
# SESION: quien esta logueado ahora
# ==========================================================

def usuario_actual():
    """Devuelve el dict del usuario logueado, o None si no hay sesion."""
    username = session.get("username")
    if username is None:
        return None
    return obtener_usuario_por_nombre(username)


def iniciar_sesion(usuario):
    session["username"] = usuario["username"]
    session.permanent = True


def cerrar_sesion():
    session.pop("username", None)


# ==========================================================
# DECORADORES DE ACCESO
# ==========================================================

def login_required(func):
    """Redirige a /auth/login si no hay sesion. Para rutas HTML."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("username") is None:
            return redirect(url_for("auth.login", next=request.path))
        return func(*args, **kwargs)
    return wrapper


def login_required_json(func):
    """Igual que login_required pero para endpoints que devuelven JSON."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if session.get("username") is None:
            return jsonify({"error": "Tenés que iniciar sesión"}), 401
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    """Exige sesion Y que el usuario tenga es_admin=True. Para rutas HTML."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None:
            return redirect(url_for("auth.login", next=request.path))
        if not usuario.get("es_admin"):
            return redirect(url_for("mezclas.index"))
        return func(*args, **kwargs)
    return wrapper


def admin_required_json(func):
    """Igual que admin_required pero para endpoints que devuelven JSON."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None:
            return jsonify({"error": "Tenés que iniciar sesión"}), 401
        if not usuario.get("es_admin"):
            return jsonify({"error": "Necesitás permisos de administrador"}), 403
        return func(*args, **kwargs)
    return wrapper