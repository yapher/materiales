"""
Generación de datos para gráficos de regresión lineal:
- Valores reales del dataset vs. valores predichos por el modelo.
- Incluye ajuste lineal (y = mx + b) y estadísticas completas.

El gráfico permite evaluar visualmente la calidad del modelo
entrenado: los puntos deberían alinearse sobre la diagonal ideal
y = x si el modelo predice perfectamente.
"""
import logging
import numpy as np
import pandas as pd

from ..constants import (
    normalizar_nombre_columna,
    MAPA_ETIQUETAS,
    MAPA_DESCRIPCIONES,
)
from ..dataset import (
    cargar_dataset,
    obtener_feature_columns,
    filtrar_dataset_entrenamiento,
)
from .state import (
    obtener_usuario,
    _modelos,
    _lock_global,
)
from .store import cargar_modelo

logger = logging.getLogger(__name__)

# ==========================================================
# CONSTANTES
# ==========================================================
K_OUTLIERS = 2.5
MAD_SCALE = 1.4826


def _obtener_modelo_por_columna(user_id, columna):
    """
    Devuelve el dict de info del modelo entrenado para una columna.
    Lanza ValueError si no existe.
    """
    if _modelos.get(user_id) is None:
        cargar_modelo()
    modelos_usuario = _modelos.get(user_id)
    if not isinstance(modelos_usuario, dict):
        raise ValueError(
            "Primero entrená el modelo para poder generar el gráfico."
        )
    if columna not in modelos_usuario:
        raise ValueError(
            f"La variable '{columna}' no está entrenada en el modelo actual."
        )
    return modelos_usuario[columna]


def _construir_X_y(info_columna, columna, df):
    """
    Construye la matriz X de features y el vector y de target
    usando exactamente las filas y columnas que se usaron
    durante el entrenamiento.
    """
    features = info_columna.get("features", [])
    if not features:
        raise ValueError(
            "El modelo no tiene features registradas."
        )

    subset = df[features + [columna]].copy()
    for col in features:
        subset[col] = pd.to_numeric(subset[col], errors="coerce")
    subset[columna] = pd.to_numeric(subset[columna], errors="coerce")
    subset = subset.dropna()

    # Excluir targets <= 0 (misma regla que el entrenamiento)
    subset = subset[subset[columna] > 0]

    X = subset[features].to_numpy(dtype=float)
    y = subset[columna].to_numpy(dtype=float)

    return X, y, subset


def _predecir_con_modelo(info_columna, X, y):
    """
    Genera predicciones del modelo entrenado para X.
    Aplica la transformación logarítmica si el modelo la usó.
    """
    modelo = info_columna["modelo"]
    usar_log = info_columna.get("log", False)

    if usar_log:
        y_log = modelo.predict(X)
        y_pred = np.expm1(y_log)
    else:
        y_pred = modelo.predict(X)

    return y_pred


def _calcular_estadisticas_regresion(y_real, y_pred):
    """
    Calcula estadísticas completas de la regresión lineal.

    Devuelve:
    - pendiente (slope del ajuste lineal)
    - intercepto
    - r2: R² del ajuste lineal (correlación²). Mide qué tan
      alineados están los puntos en una línea. Siempre >= 0.
      Es el R² más apropiado para un gráfico de regresión lineal.
    - r2_predictivo: R² del modelo predictivo (r2_score estándar).
      Mide la calidad de predicción comparada con predecir la media.
      Puede ser negativo si el modelo es peor que la media.
    - mse, rmse, mae, mape
    """
    n = len(y_real)
    if n < 2:
        return {
            "pendiente": None,
            "intercepto": None,
            "r2": None,
            "r2_predictivo": None,
            "mse": None,
            "rmse": None,
            "mae": None,
            "mape": None,
            "cantidad": n,
        }

    # Ajuste lineal: y_pred = m * y_real + b
    try:
        coef = np.polyfit(y_real, y_pred, 1)
        pendiente = float(coef[0])
        intercepto = float(coef[1])
    except Exception:
        pendiente = None
        intercepto = None

    # R² del ajuste lineal (correlación al cuadrado).
    # Mide qué tan lineal es la relación entre real y predicho.
    # Siempre >= 0. Es el R² que se muestra en el gráfico.
    try:
        std_real = np.std(y_real)
        std_pred = np.std(y_pred)
        if std_real > 1e-10 and std_pred > 1e-10:
            corr = np.corrcoef(y_real, y_pred)[0, 1]
            r2_fit = float(corr ** 2)
        else:
            r2_fit = None
    except Exception:
        r2_fit = None

    # R² predictivo (r2_score estándar).
    # Mide calidad de predicción vs. predecir la media.
    # Puede ser negativo.
    ss_res = float(np.sum((y_real - y_pred) ** 2))
    ss_tot = float(np.sum((y_real - np.mean(y_real)) ** 2))
    r2_predictivo = 1 - (ss_res / ss_tot) if ss_tot > 0 else None

    # MSE y RMSE
    mse = ss_res / n
    rmse = float(np.sqrt(mse))

    # MAE
    mae = float(np.mean(np.abs(y_real - y_pred)))

    # MAPE (evitar división por cero)
    mask_mape = np.abs(y_real) > 1e-9
    if mask_mape.sum() > 0:
        mape = float(
            np.mean(np.abs((y_real[mask_mape] - y_pred[mask_mape])
                           / y_real[mask_mape]))
            * 100.0
        )
    else:
        mape = None

    return {
        "pendiente": round(pendiente, 4) if pendiente is not None else None,
        "intercepto": round(intercepto, 4) if intercepto is not None else None,
        "r2": round(r2_fit, 4) if r2_fit is not None else None,
        "r2_predictivo": round(float(r2_predictivo), 4) if r2_predictivo is not None and np.isfinite(r2_predictivo) else None,
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "mae": round(mae, 4),
        "mape": round(mape, 2) if mape is not None else None,
        "cantidad": n,
    }


def _detectar_outliers(y_real, y_pred):
    """
    Detecta outliers mediante residuos robustos (MAD).

    Devuelve un array booleano donde True = outlier.
    """
    residuos = np.abs(y_real - y_pred)
    mediana = float(np.median(residuos))
    mad = float(np.median(np.abs(residuos - mediana)))

    if mad < 1e-10:
        umbral = float(np.percentile(residuos, 95))
    else:
        umbral = mediana + K_OUTLIERS * MAD_SCALE * mad

    return residuos > umbral, round(float(umbral), 4), round(float(mediana), 4)


def listar_variables_regresion(user_id=None):
    """
    Devuelve la lista de variables objetivo entrenadas en el modelo
    del usuario actual, con etiquetas amigables.

    Se usa para poblar el select del modal.

    Si se pasa user_id explícitamente (modo test), no se requiere
    contexto de request.
    """
    if user_id is None:
        user_id = obtener_usuario()
        if _modelos.get(user_id) is None:
            cargar_modelo()
    else:
        # Modo test: asegurar que el usuario tenga entrada en _modelos
        with _lock_global:
            if user_id not in _modelos:
                _modelos[user_id] = None

    modelos_usuario = _modelos.get(user_id)
    if not isinstance(modelos_usuario, dict):
        return []

    variables = []
    for columna in sorted(modelos_usuario.keys()):
        etiqueta = MAPA_ETIQUETAS.get(
            columna,
            columna.replace("_", " "),
        )
        descripcion = MAPA_DESCRIPCIONES.get(
            columna,
            f"Variable '{columna}' entrenada en el modelo.",
        )
        variables.append({
            "valor": columna,
            "etiqueta": etiqueta,
            "descripcion": descripcion,
        })
    return variables


def generar_grafico_regresion(columna):
    """
    Genera los datos para el gráfico de regresión lineal de una variable:
    - Valores reales del dataset
    - Valores predichos por el modelo entrenado
    - Ajuste lineal (pendiente, intercepto, R²)
    - Estadísticas completas (MSE, RMSE, MAE, MAPE)
    - Detección de outliers por residuo robusto

    Devuelve un diccionario con toda la información necesaria
    para que el frontend renderice el gráfico.
    """
    user_id = obtener_usuario()

    # Validar variable
    if not columna or not isinstance(columna, str):
        raise ValueError("Debés seleccionar una variable para graficar.")

    columna = columna.strip()

    # Obtener info del modelo
    info_columna = _obtener_modelo_por_columna(user_id, columna)

    # Cargar dataset filtrado (mismas reglas que el entrenamiento)
    df_original = cargar_dataset()
    df_filtrado, info_filtrado = filtrar_dataset_entrenamiento(df_original)

    if df_filtrado.empty:
        raise ValueError(
            "No hay filas entrenables en el dataset."
        )

    # Construir X e y
    X, y, subset = _construir_X_y(info_columna, columna, df_filtrado)

    if len(y) < 2:
        raise ValueError(
            f"Solo hay {len(y)} filas con datos válidos "
            f"para '{columna}'. Se necesitan al menos 2."
        )

    # Generar predicciones
    y_pred = _predecir_con_modelo(info_columna, X, y)

    # Detectar outliers
    mascara_outliers, umbral, mediana_residuo = _detectar_outliers(y, y_pred)
    cantidad_outliers = int(mascara_outliers.sum())

    # Estadísticas de regresión
    stats = _calcular_estadisticas_regresion(y, y_pred)

    # Construir puntos
    puntos = []
    for i in range(len(y)):
        puntos.append({
            "real": round(float(y[i]), 4),
            "predicho": round(float(y_pred[i]), 4),
            "es_outlier": bool(mascara_outliers[i]),
            "residuo": round(float(abs(y[i] - y_pred[i])), 4),
            "indice_dataset": int(subset.index[i]),
        })

    # Línea de regresión: solo 2 puntos (mínimo y máximo de y_real)
    y_min = float(y.min())
    y_max = float(y.max())
    if stats["pendiente"] is not None:
        linea_regresion = [
            {"x": y_min, "y": round(stats["pendiente"] * y_min + stats["intercepto"], 4)},
            {"x": y_max, "y": round(stats["pendiente"] * y_max + stats["intercepto"], 4)},
        ]
    else:
        linea_regresion = []

    # Línea ideal (y = x)
    linea_ideal = [
        {"x": y_min, "y": y_min},
        {"x": y_max, "y": y_max},
    ]

    etiqueta = MAPA_ETIQUETAS.get(columna, columna.replace("_", " "))
    descripcion = MAPA_DESCRIPCIONES.get(
        columna,
        f"Variable '{columna}' entrenada en el modelo.",
    )
    algoritmo = info_columna.get("algoritmo", "Desconocido")
    filas_entrenadas = info_columna.get("filas_entrenadas", len(y))

    logger.info(
        "Gráfico regresión generado para %s: %s puntos, R²=%s, outliers=%s",
        columna,
        len(puntos),
        stats["r2"],
        cantidad_outliers,
    )

    return {
        "columna": columna,
        "etiqueta": etiqueta,
        "descripcion": descripcion,
        "algoritmo": algoritmo,
        "filas_entrenadas": filas_entrenadas,
        "puntos": puntos,
        "linea_regresion": linea_regresion,
        "linea_ideal": linea_ideal,
        "stats": stats,
        "outliers": {
            "cantidad": cantidad_outliers,
            "umbral": umbral,
            "mediana_residuo": mediana_residuo,
            "k": K_OUTLIERS,
        },
        "rango": {
            "min": round(float(y.min()), 4),
            "max": round(float(y.max()), 4),
        },
    }