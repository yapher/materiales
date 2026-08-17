"""
Regresión lineal del gráfico densidad vs. temperatura.
Incluye:
- ajuste por mínimos cuadrados (densidad = m*T + b)
- puntos de la recta en cada temperatura del intervalo
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def _calcular_regresion_lineal(temperaturas, densidades):
    """
    Ajusta una regresión lineal (mínimos cuadrados) de la forma:
        densidad = pendiente * temperatura + intercepto
    sobre los puntos del gráfico densidad vs. temperatura.

    Devuelve un diccionario con:
    - pendiente: variación de densidad por Kelvin (kg/m³ / K)
    - intercepto: densidad extrapolada a T = 0
    - r2: bondad del ajuste lineal (1.0 = línea perfecta)
    - linea: dos puntos extremos de la recta para graficar
    - cantidad_puntos: cantidad de puntos usados en el ajuste

    Si hay menos de 2 puntos, devuelve None.
    """
    x = np.asarray(temperaturas, dtype=float)
    y = np.asarray(densidades, dtype=float)
    n = len(x)

    if n < 2:
        return None

    try:
        coef = np.polyfit(x, y, 1)
        pendiente = float(coef[0])
        intercepto = float(coef[1])
    except Exception:
        logger.exception("No se pudo calcular la regresión lineal")
        return None

    y_fit = pendiente * x + intercepto
    ss_res = float(np.sum((y - y_fit) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))

    if ss_tot > 0:
        r2 = 1.0 - (ss_res / ss_tot)
        if not np.isfinite(r2):
            r2 = None
    else:
        r2 = None

    x_min = float(x.min())
    x_max = float(x.max())
    linea = [
        {
            "x": x_min,
            "y": round(pendiente * x_min + intercepto, 4),
        },
        {
            "x": x_max,
            "y": round(pendiente * x_max + intercepto, 4),
        },
    ]

    return {
        "pendiente": round(pendiente, 6),
        "intercepto": round(intercepto, 4),
        "r2": round(float(r2), 4) if r2 is not None else None,
        "linea": linea,
        "cantidad_puntos": n,
    }


def _calcular_puntos_regresion_intervalos(
    regresion,
    temp_min,
    temp_max,
    intervalo,
):
    """
    Calcula los puntos de la recta de regresión lineal en cada
    temperatura del intervalo. Estos se dibujan como cuadrados rojos.

    Para cada temperatura T en [temp_min, temp_max] con paso=intervalo:
        densidad_reg = pendiente * T + intercepto

    Devuelve una lista de dicts {'temperatura', 'densidad'}.
    Si no hay regresión válida, devuelve lista vacía.
    """
    if regresion is None:
        return []

    pendiente = regresion.get("pendiente")
    intercepto = regresion.get("intercepto")
    if pendiente is None or intercepto is None:
        return []

    puntos = []
    t = temp_min
    while t <= temp_max + 1e-9:
        densidad_reg = pendiente * t + intercepto
        puntos.append({
            "temperatura": round(t, 4),
            "densidad": round(float(densidad_reg), 4),
        })
        t += intervalo

    return puntos