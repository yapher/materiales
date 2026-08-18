"""
Archivos de dataset.
Ya NO se crean copias personales por usuario.
El dataset es único y global (el maestro).
Se mantiene el módulo por compatibilidad de imports.
"""
import logging

logger = logging.getLogger(__name__)


def inicializar_dataset_usuario(user_id=None):
    """
    Ya no se inicializa un dataset por usuario.
    Se devuelve la ruta del dataset maestro.
    Se mantiene la firma de la función por compatibilidad.
    """
    from config import Config
    return Config.ARCHIVO_DATASET