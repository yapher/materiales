"""
Archivos de dataset por usuario.
"""

import os
import shutil

from config import Config
from utils import obtener_user_id, archivo_dataset_usuario


def inicializar_dataset_usuario(user_id=None):
    """
    Crea el dataset personal del usuario si todavía no existe.

    Copia el dataset maestro definido en Config.ARCHIVO_DATASET
    hacia data/users/<usuario>/dataset.xlsx.
    """
    user_id = user_id or obtener_user_id()
    archivo = archivo_dataset_usuario(user_id)

    if not os.path.exists(archivo):
        shutil.copy(
            Config.ARCHIVO_DATASET,
            archivo
        )

    return archivo