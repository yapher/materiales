"""
Fachada de compatibilidad para services/mezcla_service.py.
Este archivo ya no contiene la implementación principal.
La lógica fue movida a services/modeling/.
Se mantiene para no romper imports existentes en:
- blueprints/mezclas.py
- blueprints/admin/__init__.py
"""
from .modeling.state import (
    _modelos,
    _locks,
    _lock_global,
    _estado_entrenamiento,
    _lock_estado,
    obtener_usuario,
    obtener_lock_usuario,
    _set_estado_entrenamiento,
    obtener_estado_entrenamiento,
)
from .modeling.store import (
    cargar_modelo,
    _guardar_modelo,
    reset_modelo_service,
)
from .modeling.info import (
    _guardar_info_modelo,
    info_modelo_service,
)
from .modeling.last_prediction import (
    guardar_ultima_prediccion,
    obtener_ultima_prediccion,
)
from .modeling.training import (
    _normalizar_targets,
    iniciar_entrenamiento,
    _entrenar_en_background,
)
from .modeling.prediction import predecir_service
from .modeling.status import estado_service
from .modeling.grafico import generar_grafico_densidad
from .modeling.regresion import (
    generar_grafico_regresion,
    listar_variables_regresion,
)

__all__ = [
    # state
    "_modelos",
    "_locks",
    "_lock_global",
    "_estado_entrenamiento",
    "_lock_estado",
    "obtener_usuario",
    "obtener_lock_usuario",
    "_set_estado_entrenamiento",
    "obtener_estado_entrenamiento",
    # store
    "cargar_modelo",
    "_guardar_modelo",
    "reset_modelo_service",
    # info
    "_guardar_info_modelo",
    "info_modelo_service",
    # last prediction
    "guardar_ultima_prediccion",
    "obtener_ultima_prediccion",
    # training
    "_normalizar_targets",
    "iniciar_entrenamiento",
    "_entrenar_en_background",
    # prediction
    "predecir_service",
    # status
    "estado_service",
    # grafico
    "generar_grafico_densidad",
    # regresion
    "generar_grafico_regresion",
    "listar_variables_regresion",
]