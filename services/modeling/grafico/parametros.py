"""
Validación de parámetros del rango de temperatura
para el gráfico densidad vs. temperatura.
"""

# Cantidad máxima de puntos que se generan por consulta.
MAX_PUNTOS_POR_CONSULTA = 500


def _validar_parametros_rango(temp_min, temp_max, intervalo):
    """
    Valida y normaliza los parámetros del rango de temperatura.
    Aplica valores por defecto si no se envían.
    Lanza ValueError si los valores son inválidos.
    """
    if temp_min is None or temp_min == "":
        temp_min = 1500
    if temp_max is None or temp_max == "":
        temp_max = 2000
    if intervalo is None or intervalo == "":
        intervalo = 20

    try:
        temp_min = float(temp_min)
        temp_max = float(temp_max)
        intervalo = float(intervalo)
    except (TypeError, ValueError):
        raise ValueError(
            "Los parámetros de temperatura deben ser numéricos."
        )

    if temp_min < 0:
        raise ValueError(
            "La temperatura mínima no puede ser negativa (en K)."
        )
    if temp_max <= temp_min:
        raise ValueError(
            "La temperatura máxima debe ser mayor que la mínima."
        )
    if intervalo <= 0:
        raise ValueError(
            "El intervalo debe ser mayor que 0."
        )
    if intervalo < 1:
        raise ValueError(
            "El intervalo mínimo permitido es 1 K."
        )

    cantidad_estimada = (temp_max - temp_min) / intervalo + 1
    if cantidad_estimada > MAX_PUNTOS_POR_CONSULTA:
        raise ValueError(
            f"Se generarían {int(cantidad_estimada)} puntos, "
            "lo cual es excesivo. Aumentá el intervalo o reducí el rango "
            "(máximo 500 puntos por consulta)."
        )

    return temp_min, temp_max, intervalo