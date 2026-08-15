import logging

import numpy as np
import pandas as pd

from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)


def _debe_usar_log(columna):
    """
    Aplica transformación logarítmica en columnas que parezcan
    viscosidad, porque suelen tener distribuciones muy sesgadas.

    Se evita usar una lista fija de columnas.
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


def entrenar_una_columna(df, columnas_x, columna, n_splits=5):
    """
    Entrena un modelo para UNA columna objetivo.

    - Detecta dinámicamente features.
    - Convierte a numérico si hace falta.
    - Descarta filas incompletas.
    - Elige el mejor algoritmo por validación cruzada.
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

    subset = subset.dropna()

    if len(subset) < 10:
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