"""
Tests unitarios para services/constants.py.
Verifica la detección de columnas y generación de etiquetas.
"""

import pytest
from services.constants import (
    normalizar_nombre_columna,
    es_columna_temperatura,
    etiqueta_amigable,
    descripcion_variable,
    etiqueta_temperatura,
    SUFIJO_COMPOSICION,
    CANTIDAD_COLUMNAS_COMPOSICION,
    es_posicion_composicion,
)


class TestNormalizarNombreColumna:
    """Tests para la normalización de nombres de columna."""

    def test_minusculas(self):
        assert normalizar_nombre_columna("Temperatura") == "temperatura"

    def test_espacios_a_guiones(self):
        assert normalizar_nombre_columna("Mi Columna") == "mi_columna"

    def test_ya_normalizado(self):
        assert normalizar_nombre_columna("densidad_kg_m3") == "densidad_kg_m3"

    def test_mixto(self):
        assert normalizar_nombre_columna("Densidad Kg M3") == "densidad_kg_m3"

    def test_string_vacio(self):
        assert normalizar_nombre_columna("") == ""


class TestEsColumnaTemperatura:
    """Tests para la detección de columnas de temperatura."""

    def test_temperatura_c(self):
        assert es_columna_temperatura("Temperatura_C") is True

    def test_temperatura_k(self):
        assert es_columna_temperatura("Temperatura_K") is True

    def test_temperatura_simple(self):
        assert es_columna_temperatura("Temperatura") is True

    def test_temperature_english(self):
        assert es_columna_temperatura("Temperature_C") is True

    def test_temp_abreviado(self):
        assert es_columna_temperatura("Temp_C") is True

    def test_no_es_temperatura(self):
        assert es_columna_temperatura("Densidad_kg_m3") is False

    def test_no_es_temperatura_liquidus(self):
        """Debe rechazar variables como Temperatura_Liquidus_K."""
        assert es_columna_temperatura("Temperatura_Liquidus_K") is False

    def test_no_es_temperatura_parcial(self):
        """No debe matchear columnas que solo contienen 'temp'."""
        assert es_columna_temperatura("Tiempo_Mantenimiento_min") is False


class TestEtiquetaAmigable:
    """Tests para la generación de etiquetas amigables."""

    def test_columna_conocida(self):
        etiqueta = etiqueta_amigable("Densidad_kg_m3")
        assert "Densidad" in etiqueta

    def test_columna_desconocida(self):
        etiqueta = etiqueta_amigable("Mi_Variable_Nueva")
        assert "Mi Variable Nueva" == etiqueta

    def test_columna_con_guiones(self):
        etiqueta = etiqueta_amigable("Oxidos_Basicos_tot")
        assert " " in etiqueta  # Debe tener espacios


class TestDescripcionVariable:
    """Tests para las descripciones de variables."""

    def test_variable_conocida(self):
        desc = descripcion_variable("Densidad_kg_m3")
        assert "Densidad" in desc

    def test_variable_desconocida(self):
        desc = descripcion_variable("Variable_Nueva_X")
        assert "Variable_Nueva_X" in desc


class TestEtiquetaTemperatura:
    """Tests para la etiqueta del input de temperatura."""

    def test_columna_kelvin(self):
        etiqueta = etiqueta_temperatura("Temperatura_K")
        assert "K" in etiqueta

    def test_columna_celsius(self):
        etiqueta = etiqueta_temperatura("Temperatura_C")
        assert "°C" in etiqueta

    def test_columna_none(self):
        etiqueta = etiqueta_temperatura(None)
        assert etiqueta == "Temperatura"

    def test_columna_vacia(self):
        etiqueta = etiqueta_temperatura("")
        assert etiqueta == "Temperatura"


class TestConstantesComposicion:
    """Tests para las constantes de composición."""

    def test_sufijo_composicion(self):
        assert SUFIJO_COMPOSICION == "_pct"

    def test_cantidad_columnas_composicion(self):
        """A-K son 11 columnas."""
        assert CANTIDAD_COLUMNAS_COMPOSICION == 11

    def test_posicion_composicion_valida(self):
        """Los índices 0-10 son posición de composición."""
        assert es_posicion_composicion(0) is True
        assert es_posicion_composicion(5) is True
        assert es_posicion_composicion(10) is True

    def test_posicion_composicion_invalida(self):
        """El índice 11+ NO es posición de composición."""
        assert es_posicion_composicion(11) is False
        assert es_posicion_composicion(15) is False

    def test_posicion_negativa(self):
        assert es_posicion_composicion(-1) is False