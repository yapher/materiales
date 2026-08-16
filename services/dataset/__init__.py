"""
Paquete de dataset.

Modulariza el antiguo services/excel_service.py.

Responsabilidades:
- cache de datasets por usuario
- lectura/recarga de datasets
- detección de columnas
- features y targets
- filtros de entrenamiento
- dataset maestro
- filas de usuario
- guardado de predicciones
"""

from .cache import (
    _datasets,
    _dataset_firmas,
    _lock_dataset,
    _firma_archivo,
)

from .files import inicializar_dataset_usuario

from .loader import (
    cargar_dataset,
    recargar_dataset,
    forzar_recarga_usuario,
    dataset_cargado,
    cargar_excel_service,
)

from .schema import (
    _es_columna_numerica,
    _columnas_composicion,
    obtener_columnas_composicion,
    detectar_columna_temperatura,
    obtener_feature_columns,
    obtener_target_columns,
    obtener_esquema_dataset,
)

from .validation import (
    TOLERANCIA_SUMA_PCT,
    analizar_fila,
)

from .filters import (
    TOLERANCIA_SUMA_PCT_ENTRENAMIENTO,
    obtener_filas_entrenables,
    filtrar_dataset_entrenamiento,
)

from .listing import (
    fila_a_dict_json_seguro,
    listar_filas_df,
)

from .master import (
    _dataset_maestro,
    _dataset_maestro_firma,
    _lock_maestro,
    cargar_dataset_maestro,
    guardar_dataset_maestro,
    listar_filas_maestro,
    obtener_fila_maestro,
    actualizar_fila_maestro,
    eliminar_fila_maestro,
    agregar_fila_maestro,
)

from .user_rows import (
    listar_filas_usuario,
    obtener_fila_usuario,
    actualizar_fila_usuario,
    eliminar_fila_usuario,
)

from .prediction_writer import guardar_prediccion_en_dataset

__all__ = [
    # cache
    "_datasets",
    "_dataset_firmas",
    "_lock_dataset",
    "_firma_archivo",

    # files
    "inicializar_dataset_usuario",

    # loader
    "cargar_dataset",
    "recargar_dataset",
    "forzar_recarga_usuario",
    "dataset_cargado",
    "cargar_excel_service",

    # schema
    "_es_columna_numerica",
    "_columnas_composicion",
    "obtener_columnas_composicion",
    "detectar_columna_temperatura",
    "obtener_feature_columns",
    "obtener_target_columns",
    "obtener_esquema_dataset",

    # validation
    "TOLERANCIA_SUMA_PCT",
    "analizar_fila",

    # filters
    "TOLERANCIA_SUMA_PCT_ENTRENAMIENTO",
    "obtener_filas_entrenables",
    "filtrar_dataset_entrenamiento",

    # listing
    "fila_a_dict_json_seguro",
    "listar_filas_df",

    # master
    "_dataset_maestro",
    "_dataset_maestro_firma",
    "_lock_maestro",
    "cargar_dataset_maestro",
    "guardar_dataset_maestro",
    "listar_filas_maestro",
    "obtener_fila_maestro",
    "actualizar_fila_maestro",
    "eliminar_fila_maestro",
    "agregar_fila_maestro",

    # user rows
    "listar_filas_usuario",
    "obtener_fila_usuario",
    "actualizar_fila_usuario",
    "eliminar_fila_usuario",

    # prediction writer
    "guardar_prediccion_en_dataset",
]