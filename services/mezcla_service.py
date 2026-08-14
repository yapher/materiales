import os
import json
import time
import logging
import threading
from datetime import datetime

import joblib
import numpy as np

from .excel_service import cargar_dataset
from .ml_service import entrenar_una_columna
from .constants import ELEMENTOS, COLUMNAS, COLUMNAS_MODELO

from utils import (
    validar_mezcla_100,
    validar_temperatura,
    obtener_user_id,
    archivo_modelo_usuario,
    archivo_info_usuario,
    archivo_ultima_prediccion_usuario,
)

logger = logging.getLogger(__name__)


# ==========================================================
# MEMORIA MULTIUSUARIO
# ==========================================================

_modelos = {}          # user_id -> dict de modelos entrenados, o None
_locks = {}             # user_id -> threading.Lock (evita 2 entrenamientos del MISMO usuario en paralelo)
_lock_global = threading.Lock()  # protege la creacion de entradas en _modelos/_locks

# Estado del entrenamiento en curso (o del ultimo terminado) por usuario.
# Se consulta por POLLING desde el navegador (GET /mezclas/entrenar/estado),
# en vez de mantener una conexion SSE abierta: asi el entrenamiento sigue
# corriendo en el servidor aunque el usuario cambie de pagina, cierre la
# pestaña, o incluso cierre sesion.
_estado_entrenamiento = {}
_lock_estado = threading.Lock()


def obtener_usuario():
    """Devuelve el user_id actual y se asegura de que tenga una entrada en _modelos."""
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
    """Usado por el endpoint de polling /mezclas/entrenar/estado."""
    user_id = obtener_user_id()

    with _lock_estado:
        estado = _estado_entrenamiento.get(user_id)

    if estado is None:
        return {"corriendo": False, "listo": False}

    return dict(estado)


# ==========================================================
# CARGA / GUARDADO DE MODELO
# ==========================================================

def cargar_modelo():
    """
    Si el modelo del usuario actual no esta en memoria, intenta
    recuperarlo del disco (por ejemplo, tras un reinicio del servidor).
    """
    user_id = obtener_usuario()
    ruta = archivo_modelo_usuario()

    if _modelos[user_id] is None and os.path.exists(ruta):
        logger.info("Cargando modelo persistido del usuario %s", user_id)
        _modelos[user_id] = joblib.load(ruta)

    return _modelos[user_id]


def _guardar_modelo(user_id, modelos):
    joblib.dump(modelos, archivo_modelo_usuario(user_id))


def _guardar_info_modelo(user_id, tabla_r2, tiempo):
    info = {
        "entrenado": True,
        "usuario": user_id,
        "tabla_r2": tabla_r2,
        "tiempo_segundos": tiempo,
        "fecha": datetime.now().isoformat(timespec="seconds"),
    }

    with open(archivo_info_usuario(user_id), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

    return info


# ==========================================================
# ENTRENAMIENTO EN SEGUNDO PLANO
# ==========================================================

def iniciar_entrenamiento():
    """
    Llamado desde la vista Flask (con sesión activa: acá SÍ hay
    contexto para leer el usuario). Dispara el entrenamiento en un hilo
    de fondo y devuelve al toque; el hilo NO tiene contexto de sesión,
    por eso recibe el user_id ya resuelto como argumento y nunca llama
    a obtener_user_id() por su cuenta.

    Devuelve False si ya había un entrenamiento corriendo para este
    usuario (no dispara uno nuevo encima).
    """
    user_id = obtener_usuario()
    lock = obtener_lock_usuario(user_id)

    if not lock.acquire(blocking=False):
        return False

    _set_estado_entrenamiento(
        user_id,
        corriendo=True, listo=False, error=None,
        progreso=0, total=0, columna=None, tiempo=0,
    )

    hilo = threading.Thread(
        target=_entrenar_en_background,
        args=(user_id, lock),
        daemon=True,
    )
    hilo.start()

    return True


def _entrenar_en_background(user_id, lock):
    """
    Corre en un hilo aparte, SIN contexto de request/sesión de Flask.
    Todo lo que necesita (user_id) ya le llega por parámetro; nunca
    toca flask.session directa o indirectamente.
    """
    try:
        df = cargar_dataset(user_id)

        columnas_y = [
            c for c in df.columns[11:26]
            if c != "Temperatura_C"
        ]

        total = len(columnas_y)
        inicio = time.time()
        modelos = {}
        scores = {}

        _set_estado_entrenamiento(user_id, total=total)

        for i, columna in enumerate(columnas_y, start=1):
            try:
                info, score = entrenar_una_columna(df, COLUMNAS_MODELO, columna)

                if info:
                    modelos[columna] = info
                scores[columna] = score

                tiempo_actual = round(time.time() - inicio, 1)
                _set_estado_entrenamiento(
                    user_id, progreso=i, columna=columna, tiempo=tiempo_actual,
                )

            except Exception as e:
                logger.exception("Error entrenando columna %s (usuario %s)", columna, user_id)
                _set_estado_entrenamiento(
                    user_id, corriendo=False, listo=False,
                    error=f"Error entrenando {columna}: {e}",
                )
                return

        with _lock_global:
            _modelos[user_id] = modelos

        _guardar_modelo(user_id, modelos)

        tabla_r2 = [
            {"columna": k, "r2": v}
            for k, v in sorted(
                scores.items(),
                key=lambda x: x[1] if x[1] is not None else -1,
                reverse=True,
            )
            if v is not None
        ]

        tiempo_final = round(time.time() - inicio, 2)
        info_guardada = _guardar_info_modelo(user_id, tabla_r2, tiempo_final)

        _set_estado_entrenamiento(
            user_id,
            corriendo=False, listo=True, error=None,
            tabla_r2=tabla_r2, tiempo=tiempo_final,
            fecha=info_guardada["fecha"],
        )

    except Exception as e:
        logger.exception("Error general de entrenamiento (usuario %s)", user_id)
        _set_estado_entrenamiento(user_id, corriendo=False, listo=False, error=str(e))

    finally:
        lock.release()


# ==========================================================
# PREDICCION
# ==========================================================

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

    valores = {c: 0 for c in COLUMNAS}
    for e in mix:
        col = e["elemento"] + "_pct"
        if col in valores:
            valores[col] = e["pct"]
    valores["Temperatura_C"] = temperatura

    resultado = []

    for nombre, info in _modelos[user_id].items():
        modelo = info["modelo"]
        vector = [valores.get(f, 0) for f in info["features"]]

        pred = modelo.predict([vector])[0]

        if info["log"]:
            pred = np.expm1(pred)

        resultado.append({
            "columna": nombre,
            "prediccion": round(float(pred), 4),
        })

    return sorted(resultado, key=lambda x: x["columna"])


# ==========================================================
# ULTIMA PREDICCION (persistida en disco, sobrevive a navegar entre
# páginas, cerrar el navegador o cerrar sesión y volver a entrar)
# ==========================================================

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


# ==========================================================
# ADMIN / ESTADO
# ==========================================================

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
    }


def info_modelo_service():
    archivo = archivo_info_usuario()

    if not os.path.exists(archivo):
        return {"entrenado": False}

    with open(archivo, "r", encoding="utf-8") as f:
        return json.load(f)


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
