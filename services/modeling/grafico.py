"""
Generación de datos para gráficos derivados del modelo entrenado.
Actualmente incluye:
- Gráfico de densidad vs. temperatura (evolución térmica) con
  ajuste de regresión lineal superpuesto y puntos reales del dataset.

El gráfico muestra:
- La densidad predicha a cada temperatura del rango (composición fija).
- Una recta de regresión lineal ajustada por mínimos cuadrados:
    densidad = pendiente * temperatura + intercepto.
- Puntos cuadrados rojos sobre la recta de regresión en cada
  temperatura del intervalo.
- Los puntos REALES medidos del dataset de polvos coladores que
  tienen EXACTAMENTE la misma composición que la mezcla actual,
  con la información completa de cada fila.
"""
import logging
import numpy as np
import pandas as pd

from ..constants import normalizar_nombre_columna, MAPA_ETIQUETAS
from ..dataset import (
    cargar_dataset,
    detectar_columna_temperatura,
    obtener_columnas_composicion,
)
from .state import (
    obtener_usuario,
    _modelos,
)
from .store import cargar_modelo
from .prediction import predecir_service
from utils import validar_mezcla_100

logger = logging.getLogger(__name__)

# Cantidad máxima de puntos reales que se grafican.
MAX_PUNTOS_REALES = 500

# Tolerancia para comparar composiciones (±0.5 puntos porcentuales).
TOLERANCIA_COMPOSICION = 0.5


def _detectar_columna_densidad(user_id):
    """
    Busca en el modelo entrenado del usuario una columna cuya
    denominación normalizada contenga la palabra 'densidad'.

    Prioridad:
    1. Coincidencia exacta con 'Densidad_kg_m3' (convención del proyecto).
    2. Cualquier columna que contenga 'densidad' (case-insensitive).

    Devuelve el nombre real de la columna o None si no existe.
    """
    modelos_usuario = _modelos.get(user_id)
    if not isinstance(modelos_usuario, dict) or not modelos_usuario:
        return None

    if "Densidad_kg_m3" in modelos_usuario:
        return "Densidad_kg_m3"

    candidatas = []
    for columna in modelos_usuario.keys():
        norm = normalizar_nombre_columna(columna)
        if "densidad" in norm or "density" in norm:
            candidatas.append(columna)

    if not candidatas:
        return None

    for c in candidatas:
        if c in MAPA_ETIQUETAS:
            return c

    return candidatas[0]


def _validar_parametros_rango(temp_min, temp_max, intervalo):
    """
    Valida y normaliza los parámetros del rango de temperatura.
    Aplica valores por defecto si no se envían.
    Lanza ValueError si los valores son inválidos.
    """
    if temp_min is None or temp_min == "":
        temp_min = 1500
    if temp_max is None or temp_max == "":
        temp_max = 2000
    if intervalo is None or intervalo == "":
        intervalo = 20

    try:
        temp_min = float(temp_min)
        temp_max = float(temp_max)
        intervalo = float(intervalo)
    except (TypeError, ValueError):
        raise ValueError(
            "Los parámetros de temperatura deben ser numéricos."
        )

    if temp_min < 0:
        raise ValueError(
            "La temperatura mínima no puede ser negativa (en K)."
        )
    if temp_max <= temp_min:
        raise ValueError(
            "La temperatura máxima debe ser mayor que la mínima."
        )
    if intervalo <= 0:
        raise ValueError(
            "El intervalo debe ser mayor que 0."
        )
    if intervalo < 1:
        raise ValueError(
            "El intervalo mínimo permitido es 1 K."
        )

    cantidad_estimada = (temp_max - temp_min) / intervalo + 1
    if cantidad_estimada > 500:
        raise ValueError(
            f"Se generarían {int(cantidad_estimada)} puntos, "
            "lo cual es excesivo. Aumentá el intervalo o reducí el rango "
            "(máximo 500 puntos por consulta)."
        )

    return temp_min, temp_max, intervalo


def _calcular_regresion_lineal(temperaturas, densidades):
    """
    Ajusta una regresión lineal (mínimos cuadrados) de la forma:
        densidad = pendiente * temperatura + intercepto
    sobre los puntos del gráfico densidad vs. temperatura.

    Devuelve un diccionario con:
    - pendiente: variación de densidad por Kelvin (kg/m³ / K)
    - intercepto: densidad extrapolada a T = 0
    - r2: bondad del ajuste lineal (1.0 = línea perfecta)
    - linea: dos puntos extremos de la recta para graficar
    - cantidad_puntos: cantidad de puntos usados en el ajuste

    Si hay menos de 2 puntos, devuelve None.
    """
    x = np.asarray(temperaturas, dtype=float)
    y = np.asarray(densidades, dtype=float)
    n = len(x)
    if n < 2:
        return None

    try:
        coef = np.polyfit(x, y, 1)
        pendiente = float(coef[0])
        intercepto = float(coef[1])
    except Exception:
        logger.exception("No se pudo calcular la regresión lineal")
        return None

    y_fit = pendiente * x + intercepto
    ss_res = float(np.sum((y - y_fit) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if ss_tot > 0:
        r2 = 1.0 - (ss_res / ss_tot)
        if not np.isfinite(r2):
            r2 = None
    else:
        r2 = None

    x_min = float(x.min())
    x_max = float(x.max())
    linea = [
        {
            "x": x_min,
            "y": round(pendiente * x_min + intercepto, 4),
        },
        {
            "x": x_max,
            "y": round(pendiente * x_max + intercepto, 4),
        },
    ]

    return {
        "pendiente": round(pendiente, 6),
        "intercepto": round(intercepto, 4),
        "r2": round(float(r2), 4) if r2 is not None else None,
        "linea": linea,
        "cantidad_puntos": n,
    }


def _calcular_puntos_regresion_intervalos(regresion, temp_min, temp_max, intervalo):
    """
    Calcula los puntos de la recta de regresión lineal en cada
    temperatura del intervalo. Estos se dibujan como cuadrados rojos.

    Para cada temperatura T en [temp_min, temp_max] con paso=intervalo:
        densidad_reg = pendiente * T + intercepto

    Devuelve una lista de dicts {'temperatura', 'densidad'}.
    Si no hay regresión válida, devuelve lista vacía.
    """
    if regresion is None:
        return []

    pendiente = regresion.get("pendiente")
    intercepto = regresion.get("intercepto")

    if pendiente is None or intercepto is None:
        return []

    puntos = []
    t = temp_min
    while t <= temp_max + 1e-9:
        densidad_reg = pendiente * t + intercepto
        puntos.append({
            "temperatura": round(t, 4),
            "densidad": round(float(densidad_reg), 4),
        })
        t += intervalo

    return puntos


def _fila_a_dict_seguro(fila, columnas):
    """
    Convierte una fila de pandas a un dict JSON-safe.
    Maneja NaN, tipos numpy y valores no serializables.
    """
    resultado = {}
    for col in columnas:
        try:
            val = fila[col]
        except (KeyError, IndexError):
            resultado[col] = None
            continue

        if pd.isna(val):
            resultado[col] = None
        elif isinstance(val, (np.integer,)):
            resultado[col] = int(val)
        elif isinstance(val, (np.floating,)):
            resultado[col] = round(float(val), 4)
        elif isinstance(val, (int, float)):
            resultado[col] = round(float(val), 4) if isinstance(val, float) else val
        else:
            resultado[col] = str(val)

    return resultado


def _extraer_puntos_reales(df, columna_densidad, composicion_esperada):
    """
    Extrae del DataFrame del dataset los puntos (temperatura, densidad)
    de las filas que tienen EXACTAMENTE la misma composición que la
    mezcla actual.

    composicion_esperada es un dict:
        {"CaO_pct": 25.0, "SiO2_pct": 40.0, "MnO_pct": 35.0, ...}

    Solo se incluyen filas donde TODAS las columnas de composición
    coinciden con los valores esperados (dentro de la tolerancia).

    Cada punto incluye la información completa de la fila del dataset.

    Devuelve una lista de dicts con 'temperatura', 'densidad' y 'fila',
    ordenada por temperatura.
    """
    if df is None or df.empty:
        return []

    if columna_densidad not in df.columns:
        return []

    columna_temperatura = detectar_columna_temperatura(df.columns)
    if columna_temperatura is None or columna_temperatura not in df.columns:
        return []

    temp_serie = pd.to_numeric(
        df[columna_temperatura],
        errors="coerce",
    )
    dens_serie = pd.to_numeric(
        df[columna_densidad],
        errors="coerce",
    )

    # Máscara de coincidencia exacta de composición
    mascara_composicion = pd.Series(True, index=df.index)

    for col_pct, valor_esperado in composicion_esperada.items():
        if col_pct in df.columns:
            col_serie = pd.to_numeric(
                df[col_pct],
                errors="coerce",
            ).fillna(0)
            mascara_composicion &= (
                (col_serie - valor_esperado).abs() <= TOLERANCIA_COMPOSICION
            )

    # Máscara combinada: datos válidos + composición exacta.
    mascara_valida = (
        temp_serie.notna()
        & dens_serie.notna()
        & (dens_serie > 0)
        & mascara_composicion
    )

    # Columnas del dataset para incluir en la info de fila
    columnas_dataset = list(df.columns)

    puntos = []
    indices_validos = df.index[mascara_valida]
    for indice in indices_validos:
        fila_info = _fila_a_dict_seguro(df.loc[indice], columnas_dataset)
        puntos.append({
            "temperatura": round(float(temp_serie.at[indice]), 4),
            "densidad": round(float(dens_serie.at[indice]), 4),
            "fila": fila_info,
            "indice_dataset": int(indice),
        })

    # Ordenar por temperatura
    puntos.sort(key=lambda p: p["temperatura"])

    # Limitar la cantidad de puntos
    if len(puntos) > MAX_PUNTOS_REALES:
        paso = len(puntos) // MAX_PUNTOS_REALES + 1
        puntos = puntos[::paso]

    return puntos


def _obtener_puntos_reales_dataset(user_id, columna_densidad, mix):
    """
    Carga el dataset del usuario y extrae los puntos reales de
    densidad vs. temperatura que tienen EXACTAMENTE la misma
    composición que la mezcla actual.

    Cada punto incluye la información completa de la fila del dataset.

    Devuelve una lista de dicts {'temperatura', 'densidad', 'fila'}.
    Nunca lanza: ante cualquier problema devuelve una lista vacía.
    """
    try:
        df = cargar_dataset(user_id)
    except Exception:
        logger.warning(
            "No se pudo cargar el dataset del usuario %s para "
            "obtener puntos reales.",
            user_id,
        )
        return []

    try:
        columnas_composicion = obtener_columnas_composicion(df)
    except Exception:
        logger.warning(
            "No se pudieron detectar columnas de composición "
            "para el usuario %s.",
            user_id,
        )
        return []

    # Construir la composición esperada
    composicion_esperada = {col: 0.0 for col in columnas_composicion}

    if isinstance(mix, list):
        for elemento in mix:
            if not isinstance(elemento, dict):
                continue
            nombre = elemento.get("elemento", "")
            pct = elemento.get("pct", 0)
            col = f"{nombre}_pct"
            if col in composicion_esperada:
                try:
                    composicion_esperada[col] = float(pct)
                except (TypeError, ValueError):
                    composicion_esperada[col] = 0.0

    try:
        puntos = _extraer_puntos_reales(
            df,
            columna_densidad,
            composicion_esperada,
        )
    except Exception:
        logger.exception(
            "Error extrayendo puntos reales del dataset (usuario %s)",
            user_id,
        )
        return []

    logger.info(
        "Puntos reales del dataset para usuario %s con la misma "
        "composición: %s puntos encontrados.",
        user_id,
        len(puntos),
    )
    return puntos


def generar_grafico_densidad(mix, temp_min, temp_max, intervalo):
    """
    Genera los puntos del gráfico densidad vs. temperatura y el
    ajuste de regresión lineal correspondiente:
    1. Valida el rango de temperaturas.
    2. Valida la composición de la mezcla.
    3. Verifica que el modelo esté entrenado.
    4. Verifica que el modelo tenga una columna de densidad.
    5. Itera sobre el rango y predice la densidad a cada temperatura.
    6. Ajusta una regresión lineal densidad = m*T + b.
    7. Calcula puntos cuadrados rojos sobre la regresión en cada intervalo.
    8. Extrae los puntos reales del dataset con la MISMA composición,
       incluyendo la información completa de cada fila.
    9. Devuelve puntos, estadísticas, regresión y puntos reales.
    """
    # ==========================================================
    # 1. VALIDAR PARÁMETROS DEL RANGO
    # ==========================================================
    temp_min, temp_max, intervalo = _validar_parametros_rango(
        temp_min, temp_max, intervalo
    )

    # ==========================================================
    # 2. VALIDAR MEZCLA
    # ==========================================================
    valido, total = validar_mezcla_100(mix)
    if not valido:
        raise ValueError(
            f"La mezcla debe sumar 100% (actual {total}%)"
        )

    # ==========================================================
    # 3. VERIFICAR MODELO ENTRENADO
    # ==========================================================
    user_id = obtener_usuario()

    if _modelos.get(user_id) is None:
        cargar_modelo()
    if _modelos.get(user_id) is None:
        raise ValueError(
            "Primero entrená el modelo para poder generar el gráfico."
        )

    # ==========================================================
    # 4. DETECTAR COLUMNA DE DENSIDAD
    # ==========================================================
    columna_densidad = _detectar_columna_densidad(user_id)
    if columna_densidad is None:
        raise ValueError(
            "El modelo entrenado no contiene ninguna variable de "
            "densidad. Entrená el modelo incluyendo una columna como "
            "'Densidad_kg_m3'."
        )

    # ==========================================================
    # 5. GENERAR PUNTOS PREDICHOS
    # ==========================================================
    puntos = []
    temperaturas_pendientes = []

    t = temp_min
    while t <= temp_max + 1e-9:
        temperaturas_pendientes.append(round(t, 4))
        t += intervalo

    for temperatura in temperaturas_pendientes:
        try:
            resultado = predecir_service(mix, temperatura)
            densidad = None
            for item in resultado:
                if item.get("columna") == columna_densidad:
                    densidad = item.get("prediccion")
                    break

            if densidad is not None:
                puntos.append({
                    "temperatura": temperatura,
                    "densidad": round(float(densidad), 4),
                })
            else:
                logger.warning(
                    "No se obtuvo predicción de %s para T=%s",
                    columna_densidad,
                    temperatura,
                )
        except Exception as e:
            logger.warning(
                "Error prediciendo densidad a T=%s: %s",
                temperatura,
                e,
            )

    if not puntos:
        raise ValueError(
            "No se pudo calcular ningún punto del gráfico. "
            "Verificá que el modelo esté entrenado correctamente."
        )

    # ==========================================================
    # 6. ESTADÍSTICAS + REGRESIÓN LINEAL
    # ==========================================================
    densidades = [p["densidad"] for p in puntos]
    temperaturas = [p["temperatura"] for p in puntos]

    stats = {
        "min": round(min(densidades), 4),
        "max": round(max(densidades), 4),
        "promedio": round(sum(densidades) / len(densidades), 4),
        "cantidad": len(puntos),
        "temp_min_real": puntos[0]["temperatura"],
        "temp_max_real": puntos[-1]["temperatura"],
    }

    regresion = _calcular_regresion_lineal(temperaturas, densidades)

    # ==========================================================
    # 7. PUNTOS CUADRADOS ROJOS SOBRE LA REGRESIÓN
    #    (uno por cada temperatura del intervalo)
    # ==========================================================
    puntos_regresion_intervalos = _calcular_puntos_regresion_intervalos(
        regresion,
        temp_min,
        temp_max,
        intervalo,
    )

    # ==========================================================
    # 8. PUNTOS REALES DEL DATASET (triángulos amarillos)
    #    Solo filas con la MISMA composición exacta.
    #    Incluye la información completa de cada fila.
    # ==========================================================
    puntos_reales = _obtener_puntos_reales_dataset(
        user_id,
        columna_densidad,
        mix,
    )

    # Etiqueta amigable
    etiqueta = MAPA_ETIQUETAS.get(
        columna_densidad,
        columna_densidad.replace("_", " "),
    )

    logger.info(
        "Gráfico densidad generado: %s puntos (%s → %s K, intervalo %s), "
        "R²=%s, puntos regresión=%s, puntos reales=%s",
        len(puntos),
        temp_min,
        temp_max,
        intervalo,
        regresion["r2"] if regresion else None,
        len(puntos_regresion_intervalos),
        len(puntos_reales),
    )

    return {
        "columna": columna_densidad,
        "etiqueta": etiqueta,
        "unidad_y": "kg/m³",
        "unidad_x": "K",
        "puntos": puntos,
        "stats": stats,
        "regresion": regresion,
        "puntos_regresion_intervalos": puntos_regresion_intervalos,
        "puntos_reales": puntos_reales,
        "parametros": {
            "temp_min": temp_min,
            "temp_max": temp_max,
            "intervalo": intervalo,
        },
    }