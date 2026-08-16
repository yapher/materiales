"""
Metadatos del último entrenamiento.

Responsabilidades:
- guardar info_modelo.json
- leer info_modelo.json
- completar información faltante desde el modelo cargado
"""

import os
import json
import logging
from datetime import datetime

from utils import archivo_info_usuario

from .state import (
    obtener_usuario,
    _modelos,
)

from .store import cargar_modelo


logger = logging.getLogger(__name__)


def _guardar_info_modelo(user_id, tabla_r2, tiempo, variables_entrenadas=None):
    """
    Guarda los metadatos del último entrenamiento.
    """
    info = {
        "entrenado": True,
        "usuario": user_id,
        "tabla_r2": tabla_r2,
        "tiempo_segundos": tiempo,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "variables_entrenadas": variables_entrenadas or [],
    }

    with open(
        archivo_info_usuario(user_id),
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            info,
            f,
            ensure_ascii=False,
            indent=2
        )

    return info


def info_modelo_service():
    """
    Devuelve la información del último entrenamiento.

    Si el info_modelo.json fue generado antes de que se guardara
    la cantidad de filas entrenadas, intenta completarla desde el
    modelo.pkl cargado en memoria.
    """
    archivo = archivo_info_usuario()

    if not os.path.exists(archivo):
        return {"entrenado": False}

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception:
        logger.exception("No se pudo leer info_modelo.json")
        return {"entrenado": False}

    if not isinstance(info, dict):
        return {"entrenado": False}

    tabla = info.get("tabla_r2")

    # ------------------------------------------------------
    # Compatibilidad hacia adelante:
    # Si el info_modelo.json fue generado antes de que se
    # guardara la cantidad de filas entrenadas, intentamos
    # recuperarla desde el modelo.pkl cargado en memoria.
    # ------------------------------------------------------
    if info.get("entrenado") and isinstance(tabla, list) and tabla:
        user_id = obtener_usuario()

        try:
            if _modelos.get(user_id) is None:
                cargar_modelo()
        except Exception:
            logger.exception(
                "No se pudo cargar el modelo para completar info_modelo"
            )

        modelos_usuario = _modelos.get(user_id)

        if isinstance(modelos_usuario, dict):
            for fila in tabla:
                if not isinstance(fila, dict):
                    continue

                columna = fila.get("columna")
                info_columna = modelos_usuario.get(columna)

                if not isinstance(info_columna, dict):
                    continue

                if "filas_entrenadas" not in fila:
                    fila["filas_entrenadas"] = info_columna.get(
                        "filas_entrenadas",
                        0
                    )

                if "filas_excluidas_target_invalido" not in fila:
                    fila["filas_excluidas_target_invalido"] = info_columna.get(
                        "filas_excluidas_target_invalido",
                        0
                    )

                if "filas_excluidas_outliers" not in fila:
                    fila["filas_excluidas_outliers"] = info_columna.get(
                        "filas_excluidas_outliers",
                        0
                    )

    return info