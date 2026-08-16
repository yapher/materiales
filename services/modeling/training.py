"""
Entrenamiento de modelos.

Responsabilidades:
- normalizar variables objetivo solicitadas
- iniciar entrenamiento en background
- entrenar variable por variable
- guardar modelos y metadatos
"""

import time
import logging
import threading

from ..excel_service import (
    cargar_dataset,
    obtener_esquema_dataset,
    obtener_feature_columns,
    filtrar_dataset_entrenamiento,
)

from ..ml_service import entrenar_una_columna

from .state import (
    obtener_usuario,
    obtener_lock_usuario,
    _set_estado_entrenamiento,
    _modelos,
    _lock_global,
)

from .store import _guardar_modelo

from .info import _guardar_info_modelo


logger = logging.getLogger(__name__)


def _normalizar_targets(targets, user_id=None):
    """
    Normaliza la lista de variables a entrenar.

    Si targets es None, usa la variable por defecto detectada
    dinámicamente desde el dataset.
    """
    if targets is None:
        esquema = obtener_esquema_dataset(user_id)
        default_target = esquema.get("variable_entrenable_default")

        if not default_target:
            raise ValueError(
                "El dataset actual no tiene variables entrenables detectadas."
            )

        return [default_target]

    if not isinstance(targets, list):
        raise ValueError(
            "Las variables a modelar deben enviarse como lista"
        )

    limpias = []

    for item in targets:
        if item is None:
            continue

        valor = str(item).strip()

        if valor and valor not in limpias:
            limpias.append(valor)

    if not limpias:
        raise ValueError(
            "Seleccioná al menos una variable para modelar"
        )

    return limpias


def iniciar_entrenamiento(targets=None):
    """
    Inicia el entrenamiento en un hilo separado.

    Devuelve True si el entrenamiento comenzó.
    Devuelve False si ya hay un entrenamiento en curso
    para el mismo usuario.
    """
    user_id = obtener_usuario()
    targets = _normalizar_targets(targets, user_id)

    lock = obtener_lock_usuario(user_id)

    if not lock.acquire(blocking=False):
        return False

    _set_estado_entrenamiento(
        user_id,
        corriendo=True,
        listo=False,
        error=None,
        progreso=0,
        total=len(targets),
        columna=None,
        tiempo=0,
        variables=targets,
    )

    hilo = threading.Thread(
        target=_entrenar_en_background,
        args=(user_id, lock, targets),
        daemon=True,
    )
    hilo.start()

    return True


def _entrenar_en_background(user_id, lock, targets):
    """
    Entrenamiento real en background.

    Este método corre en un hilo separado para no bloquear
    la interfaz web.
    """
    try:
        df_original = cargar_dataset(user_id)

        # --------------------------------------------------
        # IMPORTANTE:
        # Antes de entrenar, se descartan las filas donde la
        # composición de óxidos no suma 100% (± tolerancia)
        # o donde faltan datos de composición.
        #
        # La temperatura inconsistente no excluye la fila:
        # se reemplaza por 0 dentro de
        # filtrar_dataset_entrenamiento().
        # --------------------------------------------------
        df, info_filtrado = filtrar_dataset_entrenamiento(df_original)

        logger.info(
            "Entrenamiento usuario %s: %s filas originales, "
            "%s filas entrenables, %s excluidas por composición inconsistente.",
            user_id,
            info_filtrado["filas_totales"],
            info_filtrado["filas_entrenables"],
            info_filtrado["filas_excluidas"],
        )

        if df.empty:
            _set_estado_entrenamiento(
                user_id,
                corriendo=False,
                listo=False,
                error=(
                    "No quedan filas entrenables después de filtrar las "
                    "composiciones que no suman 100%. Revisá tu dataset."
                ),
            )
            return

        features = obtener_feature_columns(df)

        if not features:
            raise ValueError(
                "No se detectaron columnas de entrada en el dataset. "
                "Se esperan columnas *_pct y, si existe, una columna de temperatura."
            )

        invalidas = [
            t for t in targets
            if t not in df.columns or t in features
        ]

        if invalidas:
            _set_estado_entrenamiento(
                user_id,
                corriendo=False,
                listo=False,
                error=f"Variables inválidas: {', '.join(invalidas)}",
            )
            return

        inicio = time.time()

        modelos = {}
        scores = {}

        _set_estado_entrenamiento(
            user_id,
            total=len(targets),
            variables=targets
        )

        for i, columna in enumerate(targets, start=1):
            try:
                info, score = entrenar_una_columna(
                    df,
                    features,
                    columna
                )

                if info:
                    modelos[columna] = info
                    scores[columna] = score

                    tiempo_actual = round(time.time() - inicio, 1)

                    _set_estado_entrenamiento(
                        user_id,
                        progreso=i,
                        columna=columna,
                        tiempo=tiempo_actual,
                    )

            except Exception as e:
                logger.exception(
                    "Error entrenando columna %s (usuario %s)",
                    columna,
                    user_id
                )

                _set_estado_entrenamiento(
                    user_id,
                    corriendo=False,
                    listo=False,
                    error=f"Error entrenando {columna}: {e}",
                )
                return

        if not modelos:
            _set_estado_entrenamiento(
                user_id,
                corriendo=False,
                listo=False,
                error=(
                    "Ninguna variable seleccionada pudo entrenarse. "
                    "Revisá que tenga datos suficientes en el dataset."
                ),
            )
            return

        with _lock_global:
            _modelos[user_id] = modelos

        _guardar_modelo(user_id, modelos)

        tabla_r2 = []

        for columna, score in sorted(
            scores.items(),
            key=lambda x: x[1] if x[1] is not None else -1,
            reverse=True
        ):
            if score is None:
                continue

            info_columna = modelos.get(columna, {}) or {}

            tabla_r2.append({
                "columna": columna,
                "r2": score,
                "filas_entrenadas": info_columna.get("filas_entrenadas", 0),
                "filas_excluidas_target_invalido": info_columna.get(
                    "filas_excluidas_target_invalido",
                    0
                ),
                "filas_excluidas_outliers": info_columna.get(
                    "filas_excluidas_outliers",
                    0
                ),
            })

        tiempo_final = round(time.time() - inicio, 2)

        info_guardada = _guardar_info_modelo(
            user_id,
            tabla_r2,
            tiempo_final,
            variables_entrenadas=targets
        )

        _set_estado_entrenamiento(
            user_id,
            corriendo=False,
            listo=True,
            error=None,
            tabla_r2=tabla_r2,
            tiempo=tiempo_final,
            fecha=info_guardada["fecha"],
            variables=targets,
            progreso=len(targets),
        )

    except Exception as e:
        logger.exception(
            "Error general de entrenamiento (usuario %s)",
            user_id
        )

        _set_estado_entrenamiento(
            user_id,
            corriendo=False,
            listo=False,
            error=str(e)
        )

    finally:
        lock.release()