"""
Métricas y cálculos estadísticos para diagnóstico.
"""

import numpy as np
import pandas as pd


def seguro_valor(valor):
    """
    Convierte un valor a algo seguro para serializar o mostrar.

    - None / NaN -> None
    - numpy int -> int
    - numpy float -> float redondeado
    - resto -> str
    """
    if valor is None:
        return None

    try:
        if pd.isna(valor):
            return None
    except Exception:
        pass

    if isinstance(valor, (int, np.integer)):
        return int(valor)

    if isinstance(valor, (float, np.floating)):
        numero = float(valor)

        if not np.isfinite(numero):
            return None

        return round(numero, 6)

    return str(valor)


def calcular_estadisticas_target(target):
    """
    Calcula estadísticas básicas de la variable objetivo.
    """
    estadisticas = {
        "cantidad": int(target.notna().sum()),
        "faltantes": int(target.isna().sum()),
        "min": None,
        "max": None,
        "media": None,
        "mediana": None,
        "desvio": None,
        "q1": None,
        "q3": None,
        "iqr": None,
    }

    target_valido = target.dropna()

    if len(target_valido) > 0:
        q1 = float(target_valido.quantile(0.25))
        q3 = float(target_valido.quantile(0.75))

        estadisticas.update({
            "min": seguro_valor(target_valido.min()),
            "max": seguro_valor(target_valido.max()),
            "media": seguro_valor(target_valido.mean()),
            "mediana": seguro_valor(target_valido.median()),
            "desvio": seguro_valor(target_valido.std()),
            "q1": seguro_valor(q1),
            "q3": seguro_valor(q3),
            "iqr": seguro_valor(q3 - q1),
        })

    return estadisticas


def calcular_outliers_target(target, entrenable, index):
    """
    Calcula outliers de la variable objetivo usando:

    - IQR
    - MAD / Z-score robusto

    Devuelve:

    - máscara de outliers
    - límite inferior
    - límite superior
    """
    y = target[entrenable]

    out_iqr = pd.Series(False, index=index)
    out_z = pd.Series(False, index=index)

    lim_inf_objetivo = None
    lim_sup_objetivo = None

    if len(y) >= 5:
        q1_objetivo = float(y.quantile(0.25))
        q3_objetivo = float(y.quantile(0.75))
        iqr_objetivo = q3_objetivo - q1_objetivo

        if iqr_objetivo > 0:
            lim_inf_objetivo = q1_objetivo - 1.5 * iqr_objetivo
            lim_sup_objetivo = q3_objetivo + 1.5 * iqr_objetivo

            out_iqr = (
                (target < lim_inf_objetivo) |
                (target > lim_sup_objetivo)
            ).fillna(False)

        med_objetivo = float(y.median())
        mad_objetivo = float(np.median(np.abs(y - med_objetivo)))

        if mad_objetivo > 0:
            z = 0.6745 * (target - med_objetivo) / mad_objetivo
            out_z = (z.abs() > 3.5).fillna(False)

    out_mask_target = (out_iqr | out_z).fillna(False)

    return out_mask_target, lim_inf_objetivo, lim_sup_objetivo


def calcular_temperaturas_atipicas(temp_series):
    """
    Calcula temperaturas atípicas usando IQR.
    """
    temp_out = pd.Series(False, index=temp_series.index)
    temp_vals = temp_series.dropna()

    if len(temp_vals) >= 5:
        q1_temp = float(temp_vals.quantile(0.25))
        q3_temp = float(temp_vals.quantile(0.75))
        iqr_temp = q3_temp - q1_temp

        if iqr_temp > 0:
            lim_inf_temp = q1_temp - 1.5 * iqr_temp
            lim_sup_temp = q3_temp + 1.5 * iqr_temp

            temp_out = (
                (temp_series < lim_inf_temp) |
                (temp_series > lim_sup_temp)
            ).fillna(False)

    return temp_out


def calcular_duplicadas_exactas(df, features, variable):
    """
    Cuenta filas duplicadas exactas considerando features + variable objetivo.
    """
    if features:
        cols_dup = list(features) + [variable]

        return int(
            df[cols_dup].duplicated(keep=False).sum()
        )

    return 0