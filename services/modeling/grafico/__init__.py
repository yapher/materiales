"""
Paquete de gráficos derivados del modelo entrenado.
Modulariza el antiguo services/modeling/grafico.py.
Responsabilidades:
- validación de parámetros del rango de temperatura
- detección de la columna de densidad en el modelo
- regresión lineal y puntos de regresión en intervalos
- extracción de puntos reales del dataset
- generación principal del gráfico densidad vs. temperatura

Mantiene los mismos nombres (públicos y privados) que el
archivo original, para no romper:
- services/modeling/__init__.py
- services/mezcla_service.py
- tests/test_grafico_densidad.py
"""

from .parametros import _validar_parametros_rango
from .densidad import _detectar_columna_densidad
from .regresion import (
    _calcular_regresion_lineal,
    _calcular_puntos_regresion_intervalos,
)
from .reales import (
    _fila_a_dict_seguro,
    _extraer_puntos_reales,
    _obtener_puntos_reales_dataset,
)
from .principal import generar_grafico_densidad

__all__ = [
    "_validar_parametros_rango",
    "_detectar_columna_densidad",
    "_calcular_regresion_lineal",
    "_calcular_puntos_regresion_intervalos",
    "_fila_a_dict_seguro",
    "_extraer_puntos_reales",
    "_obtener_puntos_reales_dataset",
    "generar_grafico_densidad",
]