import logging

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURACIÓN DEL FILTRO DE OUTLIERS
# ==========================================================

# Mínimo de filas necesarias para aplicar el filtro de outliers.
# Con menos filas, la validación cruzada no es confiable.
MIN_FILAS_PARA_FILTRO_OUTLIERS = 15

# Umbral de residuo: mediana + K * 1.4826 * MAD
# 1.4826 convierte MAD a escala de desvío estándar.
# K=3 equivale a ~3 desvíos estándar (conservador).
# K=2 sería más agresivo (elimina más filas).
K_UMBRAL_OUTLIER = 3.0


def _debe_usar_log(columna):
    """
    Aplica transformación logarítmica en columnas que parezcan
    viscosidad, porque suelen tener distribuciones muy sesgadas.
    """
    norm = str(columna).lower()
    return "viscosidad" in norm or "viscosity" in norm


def _modelos_candidatos():
    return {
        "RandomForest": RandomForestRegressor(
            n_estimators=400,
            max_depth=None,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=42,
        ),
        "ExtraTrees": ExtraTreesRegressor(
            n_estimators=400,
            min_samples_leaf=2,
            max_features="sqrt",
            random_state=42,
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=400,
            max_depth=3,
            learning_rate=0.05,
            subsample=0.8,
            random_state=42,
        ),
    }


def _evaluar_oof(modelo_base, X, y, usar_log, cv):
    preds_oof = np.zeros(len(y))

    for train_idx, test_idx in cv.split(X):
        modelo = clone(modelo_base)

        y_train = y[train_idx]
        if usar_log:
            y_train = np.log1p(y_train)

        modelo.fit(X[train_idx], y_train)
        pred = modelo.predict(X[test_idx])

        if usar_log:
            pred = np.expm1(pred)

        preds_oof[test_idx] = pred

    score = r2_score(y, preds_oof)
    if not np.isfinite(score):
        return -np.inf
    return score


# ==========================================================
# FILTRO DE OUTLIERS POR RESIDUO DE PREDICCIÓN
#
# Detecta filas inconsistentes entrenando un modelo preliminar
# y midiendo qué tan lejos está cada valor real de la predicción
# out-of-fold. Las filas con residuo anormalmente alto se
# consideran outliers y se excluyen del entrenamiento final.
#
# Este enfoque es superior a un IQR simple porque:
# - Tiene en cuenta la relación entre features y target.
# - No asume que la mayoría de un grupo es correcta.
# - Funciona para cualquier variable, sin conocer la física.
# ==========================================================

def _filtrar_outliers_por_residuo(subset, columnas_x, columna):
    """
    Detecta y excluye outliers usando predicciones out-of-fold.

    Pasos:
    1. Entrena un RandomForest rápido con validación cruzada.
    2. Obtiene predicciones OOF (cada fila predicha por un
       modelo que NO la vio).
    3. Calcula residuos = |predicción - valor real|.
    4. Define umbral = mediana + K * 1.4826 * MAD.
    5. Excluye filas con residuo > umbral.

    Devuelve: (subset_limpio, info_outliers)
    """
    n_filas = len(subset)

    if n_filas < MIN_FILAS_PARA_FILTRO_OUTLIERS:
        return subset, {
            "excluidas": 0,
            "umbral": None,
            "aplicado": False,
        }

    X = subset[columnas_x].to_numpy(dtype=float)
    y = subset[columna].to_numpy(dtype=float)

    # Modelo preliminar rápido (no necesita ser perfecto,
    # solo capturar el patrón general).
    modelo_preliminar = RandomForestRegressor(
        n_estimators=100,
        max_depth=8,
        min_samples_leaf=3,
        max_features="sqrt",
        random_state=42,
    )

    # Predicciones out-of-fold: cada fila se predice con un
    # modelo que NO la vio durante su entrenamiento.
    # Esto evita que el modelo "memorice" los outliers.
    k_cv = max(2, min(5, n_filas // 3))
    cv_preliminar = KFold(
        n_splits=k_cv,
        shuffle=True,
        random_state=42,
    )

    try:
        predicciones_oof = cross_val_predict(
            modelo_preliminar,
            X,
            y,
            cv=cv_preliminar,
        )
    except Exception:
        logger.warning(
            "Columna %s: no se pudo aplicar filtro de outliers "
            "(error en cross_val_predict). Se continúa sin filtro.",
            columna,
        )
        return subset, {
            "excluidas": 0,
            "umbral": None,
            "aplicado": False,
        }

    # Residuos absolutos.
    residuos = np.abs(y - predicciones_oof)

    # Umbral robusto: mediana + K * 1.4826 * MAD.
    # MAD (Median Absolute Deviation) es más robusto que el
    # desvío estándar cuando hay outliers presentes.
    mediana_residuo = float(np.median(residuos))
    mad_residuo = float(np.median(np.abs(residuos - mediana_residuo)))

    if mad_residuo < 1e-10:
        # Si MAD es ~0, todos los residuos son casi iguales.
        # Usar percentil 95 como fallback.
        umbral = float(np.percentile(residuos, 95))
    else:
        umbral = mediana_residuo + K_UMBRAL_OUTLIER * 1.4826 * mad_residuo

    # Identificar outliers.
    mascara_outlier = residuos > umbral
    excluidas = int(mascara_outlier.sum())

    if excluidas > 0:
        logger.info(
            "Columna %s: filtro de outliers excluye %s de %s filas "
            "(umbral=%.2f, mediana_residuo=%.2f, MAD=%.2f, K=%.1f).",
            columna,
            excluidas,
            n_filas,
            umbral,
            mediana_residuo,
            mad_residuo,
            K_UMBRAL_OUTLIER,
        )

    subset_limpio = subset[~mascara_outlier].copy()

    info = {
        "excluidas": excluidas,
        "umbral": round(umbral, 4),
        "mediana_residuo": round(mediana_residuo, 4),
        "mad_residuo": round(mad_residuo, 4),
        "aplicado": True,
    }

    return subset_limpio, info


# ==========================================================
# ENTRENAMIENTO DE UNA COLUMNA
# ==========================================================

def entrenar_una_columna(df, columnas_x, columna, n_splits=5):
    """
    Entrena un modelo para UNA columna objetivo.

    Pipeline de limpieza antes de entrenar:
    1. Convierte features y target a numérico.
    2. Descarta filas con NaN (dropna).
    3. Descarta filas donde el target es <= 0.
    4. Descarta outliers por residuo de predicción OOF.
    5. Elige el mejor algoritmo por validación cruzada.
    6. Reentrena el mejor con todos los datos limpios.
    """
    if columna not in df.columns:
        return None, None

    columnas_x = [c for c in columnas_x if c in df.columns]
    if not columnas_x:
        return None, None

    subset = df[columnas_x + [columna]].copy()

    for col in columnas_x:
        subset[col] = pd.to_numeric(subset[col], errors="coerce")

    subset[columna] = pd.to_numeric(subset[columna], errors="coerce")

    # Paso 1: eliminar filas con NaN en features o target.
    subset = subset.dropna()

    # Paso 2: excluir filas donde el target es <= 0.
    antes_target = len(subset)
    subset = subset[subset[columna] > 0]
    excluidas_target = antes_target - len(subset)

    if excluidas_target > 0:
        logger.info(
            "Columna %s: %s filas excluidas por target <= 0.",
            columna,
            excluidas_target,
        )

    # Paso 3: FILTRO DE OUTLIERS POR RESIDUO.
    # Detecta filas cuyo valor real está muy lejos de lo que
    # el modelo predice (usando predicciones out-of-fold).
    antes_outliers = len(subset)
    subset, info_outliers = _filtrar_outliers_por_residuo(
        subset,
        columnas_x,
        columna,
    )
    excluidas_outliers = antes_outliers - len(subset)

    # Si después de todos los filtros no quedan suficientes
    # filas, no se entrena.
    if len(subset) < 10:
        logger.info(
            "Columna %s: solo quedan %s filas válidas después de "
            "todos los filtros (mínimo 10). No se entrena.",
            columna,
            len(subset),
        )
        return None, None

    X = subset[columnas_x].to_numpy(dtype=float)
    y = subset[columna].to_numpy(dtype=float)

    usar_log = _debe_usar_log(columna)

    # log1p requiere valores > -1.
    if usar_log and not np.all(y > -1):
        usar_log = False

    k = max(2, min(n_splits, len(subset) // 2))
    cv = KFold(
        n_splits=k,
        shuffle=True,
        random_state=42
    )

    mejor_nombre = None
    mejor_score = -np.inf

    for nombre, modelo_base in _modelos_candidatos().items():
        try:
            score = _evaluar_oof(
                modelo_base,
                X,
                y,
                usar_log,
                cv
            )
        except Exception:
            logger.exception(
                "Fallo al evaluar %s para la columna %s",
                nombre,
                columna
            )
            score = -np.inf

        if score > mejor_score:
            mejor_score = score
            mejor_nombre = nombre

    if mejor_nombre is None:
        return None, None

    modelo_final = clone(_modelos_candidatos()[mejor_nombre])

    y_fit = np.log1p(y) if usar_log else y
    modelo_final.fit(X, y_fit)

    info = {
        "modelo": modelo_final,
        "features": columnas_x,
        "log": usar_log,
        "algoritmo": mejor_nombre,
        "filas_entrenadas": len(subset),
        "filas_excluidas_target_invalido": excluidas_target,
        "filas_excluidas_outliers": excluidas_outliers,
        "info_outliers": info_outliers,
    }

    return info, round(float(mejor_score), 4)


def entrenar_modelo(df, columnas_x, columnas_y, n_splits=5):
    modelos = {}
    scores = {}

    for columna in columnas_y:
        info, score = entrenar_una_columna(
            df,
            columnas_x,
            columna,
            n_splits
        )

        if info is not None:
            modelos[columna] = info
            scores[columna] = score

    return modelos, scores