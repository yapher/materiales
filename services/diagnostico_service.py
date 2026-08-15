import re
import logging

import numpy as np
import pandas as pd

from .excel_service import cargar_dataset

logger = logging.getLogger(__name__)

SUFIJO_COMPOSICION = "_pct"

PREFERENCIA_TEMPERATURA = [
    "Temperatura_K",
    "Temperatura_k",
    "Temperatura_C",
    "Temperatura",
    "Temperature_K",
    "Temperature_C",
    "Temperature",
    "Temp_K",
    "Temp_C",
    "Temp",
]

_PATRON_TEMPERATURA = re.compile(r"^temp(eratura|erature)?(_(k|c))?$")

TOLERANCIA_SUMA_PCT = 0.5


def normalizar_nombre_columna(columna):
    return str(columna).strip().lower().replace(" ", "_")


def es_columna_temperatura(columna):
    norm = normalizar_nombre_columna(columna)
    return bool(_PATRON_TEMPERATURA.match(norm))


def etiqueta_amigable(columna):
    return str(columna).replace("_", " ").strip()


def _es_columna_numerica(df, columna):
    if columna not in df.columns:
        return False

    if pd.api.types.is_numeric_dtype(df[columna]):
        return True

    try:
        serie = pd.to_numeric(df[columna], errors="coerce")
        return bool(serie.notna().any())
    except Exception:
        return False


def detectar_columna_temperatura(columnas):
    mapa_normalizado = {
        normalizar_nombre_columna(c): c
        for c in columnas
    }

    for nombre in PREFERENCIA_TEMPERATURA:
        clave = normalizar_nombre_columna(nombre)

        if clave in mapa_normalizado:
            return mapa_normalizado[clave]

    for col in columnas:
        if es_columna_temperatura(col):
            return col

    return None


def obtener_feature_columns(df):
    composicion = [
        c for c in df.columns
        if str(c).lower().endswith(SUFIJO_COMPOSICION)
    ]

    temperatura = detectar_columna_temperatura(df.columns)

    features = list(composicion)

    if temperatura is not None and temperatura in df.columns:
        if temperatura not in features:
            features.append(temperatura)

    return features


def obtener_target_columns(df):
    features = obtener_feature_columns(df)
    feature_set = set(features)

    columnas = list(df.columns)

    indices_features = [
        columnas.index(col)
        for col in feature_set
        if col in columnas
    ]

    if indices_features:
        inicio_targets = max(indices_features) + 1
    else:
        inicio_targets = 0

    targets = []

    for col in columnas[inicio_targets:]:
        if col in feature_set:
            continue

        if _es_columna_numerica(df, col):
            targets.append(col)

    if not targets:
        for col in columnas:
            if col in feature_set:
                continue

            if _es_columna_numerica(df, col):
                targets.append(col)

    return targets


def obtener_variables_diagnostico():
    df = cargar_dataset()

    targets = obtener_target_columns(df)

    default_target = None

    if targets:
        preferidas = [
            "Densidad_kg_m3",
            "densidad_kg_m3",
            "Densidad",
            "densidad",
        ]

        for candidata in preferidas:
            clave = normalizar_nombre_columna(candidata)

            match = next(
                (
                    t for t in targets
                    if normalizar_nombre_columna(t) == clave
                ),
                None
            )

            if match:
                default_target = match
                break

        if default_target is None:
            default_target = targets[0]

    variables = []

    for target in targets:
        variables.append({
            "valor": target,
            "etiqueta": etiqueta_amigable(target),
        })

    return variables, default_target


def _seguro_valor(valor):
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


def analizar_variable(variable):
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

    entrenable = target.notna() & features_no_nulas

    filas_entrenables = int(entrenable.sum())

    porcentaje_entrenable = 0.0

    if total_filas > 0:
        porcentaje_entrenable = round(
            100.0 * filas_entrenables / total_filas,
            2
        )

    y = target[entrenable]

    out_iqr = pd.Series(False, index=df.index)
    out_z = pd.Series(False, index=df.index)

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

    temp_out = pd.Series(False, index=df.index)

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

    duplicadas_exactas = 0

    if features:
        cols_dup = list(features) + [variable]
        duplicadas_exactas = int(
            df[cols_dup].duplicated(keep=False).sum()
        )

    razones_por_indice = {}

    def agregar_razon(indice, motivo):
        if indice not in razones_por_indice:
            razones_por_indice[indice] = []

        razones_por_indice[indice].append(motivo)

    for idx in df.index:
        if pd.isna(target.at[idx]):
            agregar_razon(idx, "Falta el valor de la variable objetivo")

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

    sospechosas = []

    for idx, razones in razones_por_indice.items():
        if not razones:
            continue

        sospechosas.append({
            "fila": posiciones.get(idx, None),
            "indice": int(idx) if isinstance(idx, (int, np.integer)) else str(idx),
            "variable": _seguro_valor(target.at[idx]),
            "temperatura": _seguro_valor(temp_series.at[idx]),
            "suma_pct": _seguro_valor(suma_pct_round.at[idx]),
            "razones": razones,
        })

    sospechosas.sort(key=lambda x: x["fila"] if x["fila"] is not None else 999999)

    total_sospechosas = len(sospechosas)

    sospechosas = sospechosas[:200]

    target_valido = target.dropna()

    estadisticas_target = {
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

    if len(target_valido) > 0:
        q1 = float(target_valido.quantile(0.25))
        q3 = float(target_valido.quantile(0.75))

        estadisticas_target.update({
            "min": _seguro_valor(target_valido.min()),
            "max": _seguro_valor(target_valido.max()),
            "media": _seguro_valor(target_valido.mean()),
            "mediana": _seguro_valor(target_valido.median()),
            "desvio": _seguro_valor(target_valido.std()),
            "q1": _seguro_valor(q1),
            "q3": _seguro_valor(q3),
            "iqr": _seguro_valor(q3 - q1),
        })

    resumen = {
        "filas_sospechosas": total_sospechosas,
        "objetivos_atipicos": int(out_mask_target.sum()),
        "suma_composicion_fuera": int(suma_fuera.sum()),
        "componentes_fuera_rango": int(comp_out_any.sum()),
        "features_faltantes": int((~features_no_nulas).sum()),
        "temperaturas_atipicas": int(temp_out.sum()),
        "duplicadas_exactas": duplicadas_exactas,
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
            "inferior": _seguro_valor(lim_inf_objetivo),
            "superior": _seguro_valor(lim_sup_objetivo),
        },
        "resumen": resumen,
        "sospechosas": sospechosas,
        "sospechosas_mostradas": len(sospechosas),
        "mensaje_lectura": mensaje_lectura,
    }