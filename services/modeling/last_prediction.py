"""
Última predicción del usuario.

Se usa para restaurar la mezcla y la tabla de predicción
cuando el usuario vuelve a entrar a la página principal.
"""

import os
import json
from datetime import datetime

from utils import archivo_ultima_prediccion_usuario


def guardar_ultima_prediccion(mix, temperatura, tabla_prediccion):
    """
    Guarda la última predicción realizada por el usuario.
    """
    datos = {
        "mix": mix,
        "temperatura": temperatura,
        "tabla_prediccion": tabla_prediccion,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }

    with open(
        archivo_ultima_prediccion_usuario(),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            datos,
            f,
            ensure_ascii=False
        )

    return datos


def obtener_ultima_prediccion():
    """
    Devuelve la última predicción guardada, o None si no existe.
    """
    archivo = archivo_ultima_prediccion_usuario()

    if not os.path.exists(archivo):
        return None

    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)