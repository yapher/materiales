import os
import json
import time
import logging
import threading
from datetime import datetime

import joblib
import numpy as np

from .excel_service import (
    cargar_dataset,
    obtener_esquema_dataset,
    obtener_feature_columns,
    filtrar_dataset_entrenamiento,
)

from .ml_service import entrenar_una_columna
from .constants import es_columna_temperatura

from utils import (
    validar_mezcla_100,
    validar_temperatura,
    obtener_user_id,
    archivo_modelo_usuario,
    archivo_info_usuario,
    archivo_ultima_prediccion_usuario,
)

logger = logging.getLogger(__name__)

_modelos = {}
_locks = {}
_lock_global = threading.Lock()

_estado_entrenamiento = {}
_lock_estado = threading.Lock()


def obtener_usuario():
    user_id = obtener_user_id()

    with _lock_global:
        if user_id not in _modelos:
            _modelos[user_id] = None

    return user_id


def obtener_lock_usuario(user_id=None):
    user_id = user_id or obtener_user_id()

    with _lock_global:
        if user_id not in _locks:
            _locks[user_id] = threading.Lock()

    return _locks[user_id]


def _set_estado_entrenamiento(user_id, **kwargs):
    with _lock_estado:
        estado = _estado_entrenamiento.setdefault(user_id, {})
        estado.update(kwargs)


def obtener_estado_entrenamiento():
    user_id = obtener_user_id()

    with _lock_estado:
        estado = _estado_entrenamiento.get(user_id)

    if estado is None:
        return {"corriendo": False, "listo": False}

    return dict(estado)


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
        raise ValueError("Las variables a modelar deben enviarse como lista")

    limpias = []

    for item in targets:
        if item is None:
            continue

        valor = str(item).strip()

        if valor and valor not in limpias:
            limpias.append(valor)

    if not limpias:
        raise ValueError("Seleccioná al menos una variable para modelar")

    return limpias


def cargar_modelo():
    user_id = obtener_usuario()
    ruta = archivo_modelo_usuario()

    if _modelos[user_id] is None and os.path.exists(ruta):
        logger.info("Cargando modelo persistido del usuario %s", user_id)
        _modelos[user_id] = joblib.load(ruta)

    return _modelos[user_id]


def _guardar_modelo(user_id, modelos):
    joblib.dump(modelos, archivo_modelo_usuario(user_id))


def _guardar_info_modelo(user_id, tabla_r2, tiempo, variables_entrenadas=None):
    info = {
        "entrenado": True,
        "usuario": user_id,
        "tabla_r2": tabla_r2,
        "tiempo_segundos": tiempo,
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "variables_entrenadas": variables_entrenadas or [],
    }

    with open(archivo_info_usuario(user_id), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    return info


def iniciar_entrenamiento(targets=None):
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
    try:
        df_original = cargar_dataset(user_id)

        # --------------------------------------------------
        # IMPORTANTE:
        # Antes de entrenar, se descartan las filas donde la
        # composición de óxidos no suma 100% (± tolerancia)
        # o donde faltan datos de composición/temperatura.
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


def predecir_service(mix, temperatura):
    user_id = obtener_usuario()

    if _modelos[user_id] is None:
        cargar_modelo()

    if _modelos[user_id] is None:
        raise ValueError("Primero entrená el modelo")

    valido, total = validar_mezcla_100(mix)

    if not valido:
        raise ValueError(f"La mezcla debe sumar 100% (actual {total}%)")

    valido, temperatura = validar_temperatura(temperatura)

    if not valido:
        raise ValueError("Temperatura inválida")

    # Juntar todas las features que conocen los modelos entrenados.
    features = set()

    for info in _modelos[user_id].values():
        features.update(info.get("features", []))

    valores = {}

    # Composición: inicializar en 0 todas las columnas *_pct conocidas.
    for feature in features:
        if str(feature).lower().endswith("_pct"):
            valores[feature] = 0.0

    # Cargar la mezcla enviada.
    for e in mix:
        elemento = e.get("elemento", "")
        pct = e.get("pct", 0)
        col = f"{elemento}_pct"

        if col in valores:
            valores[col] = float(pct)

    # Cargar temperatura en todas las features que sean temperatura.
    for feature in features:
        if es_columna_temperatura(feature):
            valores[feature] = float(temperatura)

    resultado = []

    for nombre, info in _modelos[user_id].items():
        modelo = info["modelo"]

        vector = [
            valores.get(f, 0)
            for f in info["features"]
        ]

        pred = modelo.predict([vector])[0]

        if info.get("log"):
            pred = np.expm1(pred)

        resultado.append({
            "columna": nombre,
            "prediccion": round(float(pred), 4)
        })

    return sorted(resultado, key=lambda x: x["columna"])


def guardar_ultima_prediccion(mix, temperatura, tabla_prediccion):
    datos = {
        "mix": mix,
        "temperatura": temperatura,
        "tabla_prediccion": tabla_prediccion,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }

    with open(archivo_ultima_prediccion_usuario(), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)

    return datos


def obtener_ultima_prediccion():
    archivo = archivo_ultima_prediccion_usuario()

    if not os.path.exists(archivo):
        return None

    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


def estado_service():
    user_id = obtener_usuario()

    if _modelos[user_id] is None:
        cargar_modelo()

    try:
        df = cargar_dataset()
        dataset_ok = True
        filas = len(df)
        columnas = len(df.columns)
    except Exception as e:
        logger.error("Error cargando dataset usuario %s: %s", user_id, e)
        dataset_ok = False
        filas = 0
        columnas = 0

    return {
        "usuario": user_id,
        "dataset_cargado": dataset_ok,
        "filas_dataset": filas,
        "columnas_dataset": columnas,
        "modelo_en_memoria": _modelos[user_id] is not None,
        "modelo_persistido": os.path.exists(archivo_modelo_usuario()),
        "modelo_info": info_modelo_service(),
    }


def info_modelo_service():
    archivo = archivo_info_usuario()

    if not os.path.exists(archivo):
        return {"entrenado": False}

    try:
        with open(archivo, "r", encoding="utf-8") as f:
            info = json.load(f)
    except Exception:
        logger.exception("No se pudo leer info_modelo.json")
        return {"entrenado": False}

    if not isinstance(info, dict):
        return {"entrenado": False}

    tabla = info.get("tabla_r2")

    # ------------------------------------------------------
    # Compatibilidad hacia adelante:
    # Si el info_modelo.json fue generado antes de que se
    # guardara la cantidad de filas entrenadas, intentamos
    # recuperarla desde el modelo.pkl cargado en memoria.
    # ------------------------------------------------------
    if info.get("entrenado") and isinstance(tabla, list) and tabla:
        user_id = obtener_usuario()

        try:
            if _modelos.get(user_id) is None:
                cargar_modelo()
        except Exception:
            logger.exception(
                "No se pudo cargar el modelo para completar info_modelo"
            )

        modelos_usuario = _modelos.get(user_id)

        if isinstance(modelos_usuario, dict):
            for fila in tabla:
                if not isinstance(fila, dict):
                    continue

                columna = fila.get("columna")
                info_columna = modelos_usuario.get(columna)

                if not isinstance(info_columna, dict):
                    continue

                if "filas_entrenadas" not in fila:
                    fila["filas_entrenadas"] = info_columna.get(
                        "filas_entrenadas",
                        0
                    )

                if "filas_excluidas_target_invalido" not in fila:
                    fila["filas_excluidas_target_invalido"] = info_columna.get(
                        "filas_excluidas_target_invalido",
                        0
                    )

                if "filas_excluidas_outliers" not in fila:
                    fila["filas_excluidas_outliers"] = info_columna.get(
                        "filas_excluidas_outliers",
                        0
                    )

    return info


def reset_modelo_service():
    user_id = obtener_usuario()

    with _lock_global:
        _modelos[user_id] = None

    ruta = archivo_modelo_usuario()

    if os.path.exists(ruta):
        os.remove(ruta)

    ruta_info = archivo_info_usuario()

    if os.path.exists(ruta_info):
        os.remove(ruta_info)

    with _lock_estado:
        _estado_entrenamiento.pop(user_id, None)