"""
Generación de datos para gráficos derivados del modelo entrenado.
"""
import logging
from ..constants import normalizar_nombre_columna, MAPA_ETIQUETAS
from .state import (
    obtener_usuario,
    _modelos,
)
from .store import cargar_modelo
from .prediction import predecir_service
from utils import validar_mezcla_100

logger = logging.getLogger(__name__)


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

    # Prioridad 1: nombre canónico
    if "Densidad_kg_m3" in modelos_usuario:
        return "Densidad_kg_m3"

    # Prioridad 2: búsqueda flexible
    candidatas = []
    for columna in modelos_usuario.keys():
        norm = normalizar_nombre_columna(columna)
        if "densidad" in norm or "density" in norm:
            candidatas.append(columna)

    if not candidatas:
        return None

    # Preferir la que tenga etiqueta conocida
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
    # Defaults
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

    # Limitar cantidad de puntos para evitar bloqueos
    cantidad_estimada = (temp_max - temp_min) / intervalo + 1
    if cantidad_estimada > 500:
        raise ValueError(
            f"Se generarían {int(cantidad_estimada)} puntos, "
            "lo cual es excesivo. Aumentá el intervalo o reducí el rango "
            "(máximo 500 puntos por consulta)."
        )

    return temp_min, temp_max, intervalo


def generar_grafico_densidad(mix, temp_min, temp_max, intervalo):
    """
    Genera los puntos del gráfico densidad vs. temperatura:
    1. Valida el rango de temperaturas (rápido, sin dependencias).
    2. Valida la composición de la mezcla.
    3. Verifica que el modelo esté entrenado.
    4. Verifica que el modelo tenga una columna de densidad.
    5. Itera sobre el rango y predice la densidad a cada temperatura.
    6. Devuelve los puntos y estadísticas básicas.

    El orden de validación es intencional: primero se validan los
    datos de entrada (rango, mezcla) y solo después se verifica el
    modelo. Esto permite devolver errores útiles al usuario incluso
    cuando el modelo no está entrenado, y es más eficiente.
    """
    # ==========================================================
    # 1. VALIDAR PARÁMETROS DEL RANGO (sin dependencias)
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
    # 5. GENERAR PUNTOS DEL GRÁFICO
    # ==========================================================
    puntos = []
    temperaturas_pendientes = []

    # Construir lista de temperaturas con precisión decimal
    t = temp_min
    while t <= temp_max + 1e-9:
        temperaturas_pendientes.append(round(t, 4))
        t += intervalo

    for temperatura in temperaturas_pendientes:
        try:
            resultado = predecir_service(mix, temperatura)
            # Buscar la densidad en la lista de predicciones
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
    # 6. ESTADÍSTICAS Y RESULTADO
    # ==========================================================
    densidades = [p["densidad"] for p in puntos]
    stats = {
        "min": round(min(densidades), 4),
        "max": round(max(densidades), 4),
        "promedio": round(sum(densidades) / len(densidades), 4),
        "cantidad": len(puntos),
        "temp_min_real": puntos[0]["temperatura"],
        "temp_max_real": puntos[-1]["temperatura"],
    }

    # Etiqueta amigable
    etiqueta = MAPA_ETIQUETAS.get(
        columna_densidad,
        columna_densidad.replace("_", " "),
    )

    logger.info(
        "Gráfico densidad generado: %s puntos (%s → %s K, intervalo %s)",
        len(puntos),
        temp_min,
        temp_max,
        intervalo,
    )

    return {
        "columna": columna_densidad,
        "etiqueta": etiqueta,
        "unidad_y": "kg/m³",
        "unidad_x": "K",
        "puntos": puntos,
        "stats": stats,
        "parametros": {
            "temp_min": temp_min,
            "temp_max": temp_max,
            "intervalo": intervalo,
        },
    }