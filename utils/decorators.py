import logging
from functools import wraps

from flask import jsonify

logger = logging.getLogger(__name__)


def manejar_errores_json(func):
    """
    Decorator para rutas que devuelven JSON: loguea la excepcion completa
    en el servidor (con traceback) y devuelve al cliente un mensaje
    controlado, sin filtrar detalles internos innecesarios.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # Errores de validacion: seguros para mostrar al usuario
            logger.warning("Error de validacion en %s: %s", func.__name__, e)
            return jsonify({"error": str(e)}), 400
        except Exception:
            logger.exception("Error inesperado en %s", func.__name__)
            return jsonify({"error": "Ocurrio un error interno. Revisa los logs del servidor."}), 500
    return wrapper
