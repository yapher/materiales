"""
Paquete de modelado.
Modulariza el antiguo services/mezcla_service.py.
Responsabilidades:
- estado global de modelos y entrenamiento
- carga y persistencia de modelos
- información de entrenamiento
- última predicción
- entrenamiento en background
- predicción
- estado general del sistema
- generación de gráficos derivados
"""
from .state import (
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
from .store import (
    cargar_modelo,
    _guardar_modelo,
    reset_modelo_service,
)
from .info import (
    _guardar_info_modelo,
    info_modelo_service,
)
from .last_prediction import (
    guardar_ultima_prediccion,
    obtener_ultima_prediccion,
)
from .training import (
    _normalizar_targets,
    iniciar_entrenamiento,
    _entrenar_en_background,
)
from .prediction import predecir_service
from .status import estado_service
from .grafico import generar_grafico_densidad
from .regresion import (
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