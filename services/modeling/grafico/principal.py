"""
Generación principal del gráfico densidad vs. temperatura.
Orquesta los submódulos del paquete:
1. valida parámetros y mezcla
2. verifica modelo y columna de densidad
3. genera puntos predichos
4. ajusta regresión lineal
5. extrae puntos reales del dataset
"""

import logging

from ...constants import MAPA_ETIQUETAS
from utils import validar_mezcla_100

from ..state import (
    obtener_usuario,
    _modelos,
)
from ..store import cargar_modelo
from ..prediction import predecir_service

from .parametros import _validar_parametros_rango
from .densidad import _detectar_columna_densidad
from .regresion import (
    _calcular_regresion_lineal,
    _calcular_puntos_regresion_intervalos,
)
from .reales import _obtener_puntos_reales_dataset

logger = logging.getLogger(__name__)


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
    7. Calcula puntos cuadrados rojos sobre la regresión.
    8. Extrae los puntos reales del dataset con la MISMA composición.
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
    # ==========================================================
    puntos_regresion_intervalos = _calcular_puntos_regresion_intervalos(
        regresion,
        temp_min,
        temp_max,
        intervalo,
    )

    # ==========================================================
    # 8. PUNTOS REALES DEL DATASET (triángulos amarillos)
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
        "Gráfico densidad generado: %s puntos (%s → %s K, "
        "intervalo %s), R²=%s, puntos regresión=%s, puntos reales=%s",
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