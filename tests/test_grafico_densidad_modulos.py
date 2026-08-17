"""
Tests de la modularización del gráfico densidad vs. temperatura.
Verifica que cada submódulo del paquete services/modeling/grafico/
exponga sus funciones y que la compatibilidad hacia atrás se mantenga.
"""

import pytest


class TestModulosGraficoDensidad:
    """Verifica la estructura modular del paquete."""

    def test_modulo_parametros(self):
        """parametros.py expone la validación del rango."""
        from services.modeling.grafico.parametros import (
            _validar_parametros_rango,
        )
        assert callable(_validar_parametros_rango)

    def test_modulo_densidad(self):
        """densidad.py expone la detección de columna."""
        from services.modeling.grafico.densidad import (
            _detectar_columna_densidad,
        )
        assert callable(_detectar_columna_densidad)

    def test_modulo_regresion(self):
        """regresion.py expone ajuste y puntos de intervalos."""
        from services.modeling.grafico.regresion import (
            _calcular_regresion_lineal,
            _calcular_puntos_regresion_intervalos,
        )
        assert callable(_calcular_regresion_lineal)
        assert callable(_calcular_puntos_regresion_intervalos)

    def test_modulo_reales(self):
        """reales.py expone la extracción de puntos reales."""
        from services.modeling.grafico.reales import (
            _fila_a_dict_seguro,
            _extraer_puntos_reales,
            _obtener_puntos_reales_dataset,
        )
        assert callable(_fila_a_dict_seguro)
        assert callable(_extraer_puntos_reales)
        assert callable(_obtener_puntos_reales_dataset)

    def test_modulo_principal(self):
        """principal.py expone generar_grafico_densidad."""
        from services.modeling.grafico.principal import (
            generar_grafico_densidad,
        )
        assert callable(generar_grafico_densidad)


class TestCompatibilidadPaquete:
    """El paquete re-exporta todo para no romper imports viejos."""

    def test_import_desde_paquete(self):
        """
        Los imports 'from services.modeling.grafico import ...'
        siguen funcionando igual que con el archivo monolítico.
        """
        from services.modeling.grafico import (
            generar_grafico_densidad,
            _validar_parametros_rango,
            _detectar_columna_densidad,
            _calcular_regresion_lineal,
            _calcular_puntos_regresion_intervalos,
            _fila_a_dict_seguro,
            _extraer_puntos_reales,
            _obtener_puntos_reales_dataset,
        )
        assert callable(generar_grafico_densidad)
        assert callable(_validar_parametros_rango)
        assert callable(_extraer_puntos_reales)

    def test_compatibilidad_fachada_mezcla_service(self):
        """
        services/mezcla_service.py sigue exponiendo
        generar_grafico_densidad (usado por routes_grafico.py).
        """
        from services.mezcla_service import generar_grafico_densidad
        assert callable(generar_grafico_densidad)

    def test_compatibilidad_modeling_init(self):
        """
        services/modeling/__init__.py sigue exponiendo
        generar_grafico_densidad.
        """
        from services.modeling import generar_grafico_densidad
        assert callable(generar_grafico_densidad)