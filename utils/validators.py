def validar_mezcla_100(mix, tolerancia=0.01):
    """
    Valida que la suma de porcentajes de una mezcla sea 100.

    Se usa una pequeña tolerancia para evitar problemas por
    redondeo floating point.

    Devuelve (es_valido, total).
    """
    total = 0.0

    for e in mix:
        try:
            total += float(e.get("pct", 0))
        except (TypeError, ValueError):
            total += 0.0

    return abs(total - 100) <= tolerancia, total


def validar_temperatura(valor):
    """
    Intenta convertir a float.

    Devuelve (es_valido, valor_o_none).
    """
    try:
        return True, float(valor)
    except (TypeError, ValueError):
        return False, None