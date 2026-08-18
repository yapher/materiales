"""
Operaciones sobre filas del dataset.
Ahora el dataset es GLOBAL: las operaciones de lectura son para
todos los usuarios, las de escritura solo para admin.
Se mantiene el módulo por compatibilidad de imports.
"""
import logging
from .master import (
    listar_filas_maestro,
    obtener_fila_maestro,
    actualizar_fila_maestro,
    eliminar_fila_maestro,
)

logger = logging.getLogger(__name__)


def listar_filas_usuario():
    """
    Lista las filas del dataset global.
    Compatible con el nombre anterior.
    """
    return listar_filas_maestro()


def obtener_fila_usuario(indice):
    """
    Devuelve columnas y una fila del dataset global.
    """
    return obtener_fila_maestro(indice)


def actualizar_fila_usuario(indice, valores):
    """
    Actualiza una fila del dataset global.
    Solo debe ser llamado por admin (la ruta lo verifica).
    """
    return actualizar_fila_maestro(indice, valores)


def eliminar_fila_usuario(indice):
    """
    Elimina una fila del dataset global.
    Solo debe ser llamado por admin (la ruta lo verifica).
    """
    return eliminar_fila_maestro(indice)