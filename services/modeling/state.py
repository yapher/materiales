"""
Estado global del modelado por usuario.

Acá viven:
- modelos cargados en memoria
- locks por usuario
- lock global
- estado de entrenamiento
"""

import threading

from utils import obtener_user_id


# ==========================================================
# MODELOS POR USUARIO
# ==========================================================
_modelos = {}

# ==========================================================
# LOCKS
# ==========================================================
_locks = {}
_lock_global = threading.Lock()

# ==========================================================
# ESTADO DE ENTRENAMIENTO
# ==========================================================
_estado_entrenamiento = {}
_lock_estado = threading.Lock()


def obtener_usuario():
    """
    Devuelve el user_id actual y asegura que tenga una entrada
    en el diccionario de modelos.
    """
    user_id = obtener_user_id()

    with _lock_global:
        if user_id not in _modelos:
            _modelos[user_id] = None

    return user_id


def obtener_lock_usuario(user_id=None):
    """
    Devuelve el lock específico del usuario.

    Esto evita que un mismo usuario dispare dos entrenamientos
    en paralelo, sin bloquear a otros usuarios.
    """
    user_id = user_id or obtener_user_id()

    with _lock_global:
        if user_id not in _locks:
            _locks[user_id] = threading.Lock()

    return _locks[user_id]


def _set_estado_entrenamiento(user_id, **kwargs):
    """
    Actualiza el estado de entrenamiento del usuario.
    """
    with _lock_estado:
        estado = _estado_entrenamiento.setdefault(user_id, {})
        estado.update(kwargs)


def obtener_estado_entrenamiento():
    """
    Devuelve una copia del estado de entrenamiento del usuario actual.
    """
    user_id = obtener_user_id()

    with _lock_estado:
        estado = _estado_entrenamiento.get(user_id)

    if estado is None:
        return {
            "corriendo": False,
            "listo": False,
        }

    return dict(estado)