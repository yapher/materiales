"""
Análisis principal de diagnóstico para una variable objetivo.
"""

import numpy as np
import pandas as pd

from ..excel_service import (
    cargar_dataset,
    obtener_filas_entrenables,
    obtener_feature_columns,
    detectar_columna_temperatura,
)

from ..constants import (
    SUFIJO_COMPOSICION,
    etiqueta_amigable,
)

from .metrics import (
    calcular_estadisticas_target,
    calcular_outliers_target,
    calcular_temperaturas_atipicas,
    calcular_duplicadas_exactas,
)

from .reasons import (
    construir_razones_por_indice,
    construir_sospechosas,
)


TOLERANCIA_SUMA_PCT = 0.5


def analizar_variable(variable):
    """
    Analiza una variable objetivo del dataset y detecta:

    1. Filas donde la composición no suma 100%.
    2. Filas donde el target es <= 0.
    3. Filas donde la temperatura es inconsistente.
    4. Filas con features faltantes.
    5. Outliers del target.
    6. Temperaturas atípicas.
    7. Duplicadas exactas.
    """
    df = cargar_dataset().copy()

    if variable not in df.columns:
        raise ValueError(
            f"La columna '{variable}' no existe en el dataset actual."
        )

    features = obtener_feature_columns(df)

    if variable in features:
        raise ValueError(
            f"'{variable}' es una columna de entrada, no una variable objetivo."
        )

    target = pd.to_numeric(df[variable], errors="coerce")

    if target.notna().sum() == 0:
        raise ValueError(
            f"La variable '{variable}' no contiene valores numéricos válidos."
        )

    total_filas = len(df)

    posiciones = {
        idx: i + 1
        for i, idx in enumerate(df.index)
    }

    temp_col = detectar_columna_temperatura(df.columns)

    composicion = [
        c for c in features
        if str(c).lower().endswith(SUFIJO_COMPOSICION)
    ]

    if features:
        feat_df = df[features].apply(pd.to_numeric, errors="coerce")
        features_no_nulas = feat_df.notna().all(axis=1)
    else:
        feat_df = pd.DataFrame(index=df.index)
        features_no_nulas = pd.Series(True, index=df.index)

    if composicion:
        comp_df = feat_df[composicion]
        comp_no_nulas = comp_df.notna().all(axis=1)

        suma_pct = comp_df.sum(axis=1)
        suma_pct_round = suma_pct.round(2)

        suma_fuera = comp_no_nulas & (
            (suma_pct < 100 - TOLERANCIA_SUMA_PCT) |
            (suma_pct > 100 + TOLERANCIA_SUMA_PCT)
        )

        comp_out = (comp_df < 0) | (comp_df > 100)
        comp_out_any = comp_out.any(axis=1)
    else:
        suma_pct = pd.Series(np.nan, index=df.index)
        suma_pct_round = pd.Series(np.nan, index=df.index)
        suma_fuera = pd.Series(False, index=df.index)
        comp_out_any = pd.Series(False, index=df.index)

    if temp_col and temp_col in feat_df.columns:
        temp_series = feat_df[temp_col]
    else:
        temp_series = pd.Series(np.nan, index=df.index)

    # ----------------------------------------------------------
    # FILTRO DE COMPOSICIÓN
    # ----------------------------------------------------------
    mascara_composicion_ok = obtener_filas_entrenables(df)

    # ----------------------------------------------------------
    # FILTRO DE TARGET
    # ----------------------------------------------------------
    target_valido_positivo = target > 0

    # ----------------------------------------------------------
    # TEMPERATURA INCONSISTENTE
    # ----------------------------------------------------------
    temperatura_inconsistente = temp_series.isna()
    cant_temp_reemplazada = int(temperatura_inconsistente.sum())

    # ----------------------------------------------------------
    # MÁSCARA DE ENTRENABLE
    # ----------------------------------------------------------
    entrenable = (
        target.notna()
        & features_no_nulas
        & mascara_composicion_ok
        & target_valido_positivo
    )

    filas_entrenables = int(entrenable.sum())

    porcentaje_entrenable = 0.0
    if total_filas > 0:
        porcentaje_entrenable = round(
            100.0 * filas_entrenables / total_filas,
            2
        )

    excluidas_por_composicion = int(
        (
            target.notna()
            & features_no_nulas
            & ~mascara_composicion_ok
        ).sum()
    )

    excluidas_por_target_cero = int(
        (
            target.notna()
            & features_no_nulas
            & mascara_composicion_ok
            & ~target_valido_positivo
        ).sum()
    )

    # ----------------------------------------------------------
    # OUTLIERS Y TEMPERATURAS ATÍPICAS
    # ----------------------------------------------------------
    out_mask_target, lim_inf_objetivo, lim_sup_objetivo = calcular_outliers_target(
        target,
        entrenable,
        df.index
    )

    temp_out = calcular_temperaturas_atipicas(temp_series)

    duplicadas_exactas = calcular_duplicadas_exactas(
        df,
        features,
        variable
    )

    # ----------------------------------------------------------
    # RAZONES POR FILA
    # ----------------------------------------------------------
    razones_por_indice = construir_razones_por_indice(
        df=df,
        target=target,
        features=features,
        feat_df=feat_df,
        features_no_nulas=features_no_nulas,
        suma_pct_round=suma_pct_round,
        suma_fuera=suma_fuera,
        comp_out_any=comp_out_any,
        temperatura_inconsistente=temperatura_inconsistente,
        out_mask_target=out_mask_target,
        temp_out=temp_out,
    )

    sospechosas = construir_sospechosas(
        razones_por_indice=razones_por_indice,
        posiciones=posiciones,
        target=target,
        temp_series=temp_series,
        suma_pct_round=suma_pct_round,
    )

    total_sospechosas = len(sospechosas)
    sospechosas = sospechosas[:200]

    estadisticas_target = calcular_estadisticas_target(target)

    resumen = {
        "filas_sospechosas": total_sospechosas,
        "objetivos_atipicos": int(out_mask_target.sum()),
        "suma_composicion_fuera": int(suma_fuera.sum()),
        "componentes_fuera_rango": int(comp_out_any.sum()),
        "features_faltantes": int((~features_no_nulas).sum()),
        "temperaturas_atipicas": int(temp_out.sum()),
        "duplicadas_exactas": duplicadas_exactas,
        "excluidas_por_composicion": excluidas_por_composicion,
        "excluidas_por_target_cero": excluidas_por_target_cero,
        "temperatura_reemplazada_por_0": cant_temp_reemplazada,
    }

    problemas = []

    if resumen["objetivos_atipicos"] > 0:
        problemas.append(
            f"{resumen['objetivos_atipicos']} objetivos atípicos"
        )

    if resumen["suma_composicion_fuera"] > 0:
        problemas.append(
            f"{resumen['suma_composicion_fuera']} filas con composición fuera de 100%"
        )

    if resumen["componentes_fuera_rango"] > 0:
        problemas.append(
            f"{resumen['componentes_fuera_rango']} filas con componentes fuera de rango"
        )

    if resumen["features_faltantes"] > 0:
        problemas.append(
            f"{resumen['features_faltantes']} filas con valores faltantes en features"
        )

    if resumen["excluidas_por_target_cero"] > 0:
        problemas.append(
            f"{resumen['excluidas_por_target_cero']} filas con {etiqueta_amigable(variable)} ≤ 0"
        )

    if resumen["temperaturas_atipicas"] > 0:
        problemas.append(
            f"{resumen['temperaturas_atipicas']} temperaturas atípicas"
        )

    if resumen["duplicadas_exactas"] > 0:
        problemas.append(
            f"{resumen['duplicadas_exactas']} filas duplicadas exactas"
        )

    if problemas:
        mensaje_lectura = (
            "Se detectaron posibles problemas: "
            + ", ".join(problemas)
            + ". Revisá las filas marcadas antes de borrarlas; solo corregí o eliminá "
            "las que realmente sean errores de carga o medición."
        )
    else:
        mensaje_lectura = (
            "No se detectaron inconsistencias evidentes en el dataset para esta variable. "
            "Si el R² sigue bajo, puede deberse a falta de datos representativos, "
            "ruido experimental o variables físicas que no están incluidas como features."
        )

    info_entrenamiento = []

    if excluidas_por_composicion > 0:
        info_entrenamiento.append(
            f"{excluidas_por_composicion} filas no se usarán al entrenar "
            "porque su composición no suma 100% o tiene porcentajes faltantes."
        )

    if excluidas_por_target_cero > 0:
        info_entrenamiento.append(
            f"{excluidas_por_target_cero} filas no se usarán al entrenar "
            f"porque {etiqueta_amigable(variable)} es ≤ 0."
        )

    if cant_temp_reemplazada > 0:
        info_entrenamiento.append(
            f"{cant_temp_reemplazada} filas tienen temperatura inconsistente; "
            "se reemplazará por 0 al entrenar (no se excluyen)."
        )

    if info_entrenamiento:
        mensaje_lectura += " " + " ".join(info_entrenamiento)

    return {
        "variable": variable,
        "etiqueta_variable": etiqueta_amigable(variable),
        "total_filas": total_filas,
        "filas_con_target": int(target.notna().sum()),
        "filas_entrenables": filas_entrenables,
        "porcentaje_entrenable": porcentaje_entrenable,
        "features": features,
        "temperatura_column": temp_col,
        "estadisticas_target": estadisticas_target,
        "limites_objetivo": {
            "inferior": lim_inf_objetivo,
            "superior": lim_sup_objetivo,
        },
        "resumen": resumen,
        "sospechosas": sospechosas,
        "sospechosas_mostradas": len(sospechosas),
        "mensaje_lectura": mensaje_lectura,
    }