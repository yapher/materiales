"""
Predicción de propiedades para una mezcla dada.
"""

import numpy as np

from ..excel_service import obtener_esquema_dataset
from ..constants import es_columna_temperatura

from utils import (
    validar_mezcla_100,
    validar_temperatura,
)

from .state import (
    obtener_usuario,
    _modelos,
)

from .store import cargar_modelo


def predecir_service(mix, temperatura):
    """
    Predice todas las variables entrenadas para una mezcla
    y una temperatura dadas.
    """
    user_id = obtener_usuario()

    if _modelos[user_id] is None:
        cargar_modelo()

    if _modelos[user_id] is None:
        raise ValueError("Primero entrená el modelo")

    # ==========================================================
    # Validación de compatibilidad del modelo con el dataset actual.
    #
    # Si el modelo fue entrenado con una versión anterior donde
    # variables objetivo terminadas en '_pct' fueron detectadas
    # incorrectamente como composición, ese modelo ya no es válido.
    #
    # Ejemplo: si el modelo usa como feature una columna que hoy
    # el dataset considera variable entrenable, la predicción puede
    # estar contaminada. En ese caso se pide borrar y reentrenar.
    # ==========================================================
    try:
        esquema_actual = obtener_esquema_dataset(user_id)
        features_actuales = set(esquema_actual.get("features", []))
    except Exception:
        features_actuales = None

    if features_actuales is not None and isinstance(_modelos[user_id], dict):
        features_invalidas = []

        for info in _modelos[user_id].values():
            for feature in info.get("features", []):
                if (
                    feature not in features_actuales
                    and feature not in features_invalidas
                ):
                    features_invalidas.append(feature)

        if features_invalidas:
            raise ValueError(
                "El modelo entrenado usa columnas que el dataset actual "
                "ya no considera features "
                f"({', '.join(features_invalidas)}). "
                "Borrá el modelo desde el panel de Admin y reentrená."
            )

    valido, total = validar_mezcla_100(mix)

    if not valido:
        raise ValueError(
            f"La mezcla debe sumar 100% (actual {total}%)"
        )

    valido, temperatura = validar_temperatura(temperatura)

    if not valido:
        raise ValueError("Temperatura inválida")

    # Juntar todas las features que conocen los modelos entrenados.
    features = set()

    for info in _modelos[user_id].values():
        features.update(info.get("features", []))

    valores = {}

    # Composición: inicializar en 0 todas las columnas *_pct conocidas.
    for feature in features:
        if str(feature).lower().endswith("_pct"):
            valores[feature] = 0.0

    # Cargar la mezcla enviada.
    for e in mix:
        elemento = e.get("elemento", "")
        pct = e.get("pct", 0)

        col = f"{elemento}_pct"

        if col in valores:
            valores[col] = float(pct)

    # Cargar temperatura en todas las features que sean temperatura.
    for feature in features:
        if es_columna_temperatura(feature):
            valores[feature] = float(temperatura)

    resultado = []

    for nombre, info in _modelos[user_id].items():
        modelo = info["modelo"]

        vector = [
            valores.get(f, 0)
            for f in info["features"]
        ]

        pred = modelo.predict([vector])[0]

        if info.get("log"):
            pred = np.expm1(pred)

        resultado.append({
            "columna": nombre,
            "prediccion": round(float(pred), 4)
        })

    return sorted(
        resultado,
        key=lambda x: x["columna"]
    )