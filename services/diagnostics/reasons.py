"""
Construcción de motivos y filas sospechosas para diagnóstico.
"""

import pandas as pd

from .metrics import seguro_valor


def construir_razones_por_indice(
    df,
    target,
    features,
    feat_df,
    features_no_nulas,
    suma_pct_round,
    suma_fuera,
    comp_out_any,
    temperatura_inconsistente,
    out_mask_target,
    temp_out,
):
    """
    Construye una lista de motivos por fila para mostrar
    en la tabla de filas sospechosas.
    """
    razones_por_indice = {}

    def agregar_razon(indice, motivo):
        if indice not in razones_por_indice:
            razones_por_indice[indice] = []

        razones_por_indice[indice].append(motivo)

    for idx in df.index:
        if pd.isna(target.at[idx]):
            agregar_razon(
                idx,
                "Falta el valor de la variable objetivo"
            )

        if not bool(features_no_nulas.at[idx]):
            faltantes = []

            for c in features:
                if pd.isna(feat_df.at[idx, c]):
                    faltantes.append(c)

            if len(faltantes) > 3:
                agregar_razon(
                    idx,
                    f"Faltan valores en {len(faltantes)} columnas de entrada"
                )
            else:
                agregar_razon(
                    idx,
                    "Faltan valores en: " + ", ".join(faltantes)
                )

        if bool(suma_fuera.at[idx]):
            agregar_razon(
                idx,
                f"La composición suma {suma_pct_round.at[idx]}%"
            )

        if bool(comp_out_any.at[idx]):
            agregar_razon(
                idx,
                "Hay componentes fuera de rango 0-100%"
            )

        if bool(target.at[idx] <= 0) and not pd.isna(target.at[idx]):
            agregar_razon(
                idx,
                f"Valor objetivo ≤ 0 ({seguro_valor(target.at[idx])}): "
                "se excluye del entrenamiento"
            )

        if bool(temperatura_inconsistente.at[idx]):
            agregar_razon(
                idx,
                "Temperatura inconsistente: se reemplaza por 0 al entrenar"
            )

        if bool(out_mask_target.at[idx]):
            agregar_razon(
                idx,
                "Valor objetivo atípico"
            )

        if bool(temp_out.at[idx]):
            agregar_razon(
                idx,
                "Temperatura atípica"
            )

    return razones_por_indice


def construir_sospechosas(
    razones_por_indice,
    posiciones,
    target,
    temp_series,
    suma_pct_round,
):
    """
    Convierte el diccionario de razones en una lista de filas
    sospechosas lista para mostrar en la UI.
    """
    sospechosas = []

    for idx, razones in razones_por_indice.items():
        if not razones:
            continue

        sospechosas.append({
            "fila": posiciones.get(idx, None),
            "indice": int(idx) if isinstance(idx, (int,)) else str(idx),
            "variable": seguro_valor(target.at[idx]),
            "temperatura": seguro_valor(temp_series.at[idx]),
            "suma_pct": seguro_valor(suma_pct_round.at[idx]),
            "razones": razones,
        })

    sospechosas.sort(
        key=lambda x: x["fila"] if x["fila"] is not None else 999999
    )

    return sospechosas