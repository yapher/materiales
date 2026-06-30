import numpy as np
from sklearn.base import clone
from sklearn.ensemble import (
    RandomForestRegressor,
    GradientBoostingRegressor,
    ExtraTreesRegressor,
)
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score


# Variables muy "sesgadas" (muchos valores chicos, pocos grandes),
# donde conviene entrenar en escala logaritmica. Es un truco estandar
# para viscosidad, que suele variar en varios ordenes de magnitud.
COLUMNAS_LOG = {"Viscosidad_Pa_s"}


def _modelos_candidatos():
    """Devuelve instancias NUEVAS de cada modelo candidato."""
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
    """
    Validacion cruzada "out-of-fold": en cada fold se entrena con una
    parte de los datos y se predice la parte que el modelo NO vio.
    El R2 se calcula sobre esas predicciones honestas, nunca sobre
    datos de entrenamiento (a diferencia de model.score(X, y)).
    """

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
    """
    Entrena (con seleccion automatica de modelo + validacion cruzada)
    UNA SOLA columna objetivo.

    Se separo del loop principal (antes en entrenar_modelo)
    para que state.py pueda llamarla columna por columna y reportar
    progreso/tiempo transcurrido en vivo, en vez de bloquear todo de
    una sola vez sin feedback.

    Devuelve:
        info:  dict {"modelo", "features", "log", "algoritmo"} o None
               si no habia datos suficientes
        score: r2 (float) por validacion cruzada, o None
    """

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
            score = -np.inf

        if score > mejor_score:
            mejor_score = score
            mejor_nombre = nombre

    # Reentrenamos el mejor algoritmo con TODOS los datos disponibles
    # para esa columna (se usa despues en /predecir).
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
    """
    Entrena TODAS las columnas de una sola vez (sin progreso intermedio).
    Se mantiene como utilidad simple; state.py usa entrenar_una_columna
    directamente para poder mostrar el contador en vivo.
    """

    modelos = {}
    scores = {}

    for columna in columnas_y:
        info, score = entrenar_una_columna(df, columnas_x, columna, n_splits)
        if info is not None:
            modelos[columna] = info
        scores[columna] = score

    return modelos, scores
