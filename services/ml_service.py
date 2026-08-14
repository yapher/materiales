import logging

import numpy as np
from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score

logger = logging.getLogger(__name__)

COLUMNAS_LOG = {"Viscosidad_Pa_s"}


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

    return r2_score(y, preds_oof)


def entrenar_una_columna(df, columnas_x, columna, n_splits=5):
    usar_log = columna in COLUMNAS_LOG

    subset = df[columnas_x + [columna]].dropna()

    if len(subset) < 10:
        return None, None

    X = subset[columnas_x].to_numpy()
    y = subset[columna].to_numpy()

    k = max(2, min(n_splits, len(subset) // 2))
    cv = KFold(n_splits=k, shuffle=True, random_state=42)

    mejor_nombre = None
    mejor_score = -np.inf

    for nombre, modelo_base in _modelos_candidatos().items():
        try:
            score = _evaluar_oof(modelo_base, X, y, usar_log, cv)
        except Exception:
            logger.exception("Fallo al evaluar %s para la columna %s", nombre, columna)
            score = -np.inf

        if score > mejor_score:
            mejor_score = score
            mejor_nombre = nombre

    modelo_final = _modelos_candidatos()[mejor_nombre]
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
        info, score = entrenar_una_columna(df, columnas_x, columna, n_splits)
        if info is not None:
            modelos[columna] = info
        scores[columna] = score

    return modelos, scores
