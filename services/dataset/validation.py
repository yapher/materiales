"""
Validación de filas de dataset.
"""

import pandas as pd

TOLERANCIA_SUMA_PCT = 0.5


def analizar_fila(fila, columnas_pct, columna_temperatura=None):
    """
    Analiza una fila del dataset y detecta inconsistencias.

    Una fila se marca como inconsistente si:

    - faltan valores en columnas de composición
    - falta la temperatura, si existe columna de temperatura
    - la suma de composición no da 100 ± tolerancia
    """
    motivos = []

    columnas_obligatorias = list(columnas_pct)

    if columna_temperatura is not None and columna_temperatura in fila.index:
        columnas_obligatorias.append(columna_temperatura)

    faltantes = [
        c for c in columnas_obligatorias
        if pd.isna(fila.get(c))
    ]

    if faltantes:
        motivos.append(f"Faltan valores en: {', '.join(faltantes)}")

    presentes = [
        c for c in columnas_pct
        if not pd.isna(fila.get(c))
    ]

    if presentes:
        suma = sum(fila.get(c, 0) for c in presentes)

        if abs(suma - 100) > TOLERANCIA_SUMA_PCT:
            motivos.append(
                f"La composición suma {round(suma, 2)}%, no 100%"
            )

    if motivos:
        return True, "; ".join(motivos)

    return False, None