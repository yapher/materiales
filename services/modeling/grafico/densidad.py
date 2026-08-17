"""
Detección de la columna de densidad dentro del modelo entrenado.
"""

from ...constants import normalizar_nombre_columna, MAPA_ETIQUETAS
from ..state import _modelos


def _detectar_columna_densidad(user_id):
    """
    Busca en el modelo entrenado del usuario una columna cuya
    denominación normalizada contenga la palabra 'densidad'.
    Prioridad:
    1. Coincidencia exacta con 'Densidad_kg_m3' (convención del proyecto).
    2. Cualquier columna que contenga 'densidad' (case-insensitive).
    Devuelve el nombre real de la columna o None si no existe.
    """
    modelos_usuario = _modelos.get(user_id)
    if not isinstance(modelos_usuario, dict) or not modelos_usuario:
        return None

    if "Densidad_kg_m3" in modelos_usuario:
        return "Densidad_kg_m3"

    candidatas = []
    for columna in modelos_usuario.keys():
        norm = normalizar_nombre_columna(columna)
        if "densidad" in norm or "density" in norm:
            candidatas.append(columna)

    if not candidatas:
        return None

    for c in candidatas:
        if c in MAPA_ETIQUETAS:
            return c

    return candidatas[0]