def validar_mezcla_100(mix):
    """
    Valida que la suma de porcentajes de una mezcla sea 100.
    Devuelve (es_valido, total).
    """
    total = sum(e.get("pct", 0) for e in mix)
    return total == 100, total


def validar_temperatura(valor):
    """
    Intenta convertir a float. Devuelve (es_valido, valor_o_none).
    """
    try:
        return True, float(valor)
    except (TypeError, ValueError):
        return False, None
