"""
Tests para services/excel_service.py.
Verifica la detección de columnas y el esquema del dataset.
"""

import pytest
import pandas as pd
from services.excel_service import (
    _columnas_composicion,
    detectar_columna_temperatura,
    obtener_feature_columns,
    obtener_target_columns,
    _es_columna_numerica,
)


@pytest.fixture
def sample_dataframe():
    """DataFrame de ejemplo con estructura de dataset real."""
    data = {
        # Composición (A-K)
        "CaO_pct": [40.0, 35.0],
        "SiO2_pct": [30.0, 32.0],
        "Al2O3_pct": [10.0, 12.0],
        "MgO_pct": [5.0, 6.0],
        "Na2O_pct": [3.0, 2.5],
        "K2O_pct": [2.0, 2.5],
        "Li2O_pct": [1.0, 1.0],
        "CaF2_pct": [4.0, 4.0],
        "Fe2O3_pct": [2.0, 2.0],
        "MnO_pct": [1.5, 1.5],
        "TiO2_pct": [1.5, 1.5],
        # Temperatura
        "Temperatura_C": [1500, 1550],
        # Variables objetivo (L+)
        "Densidad_kg_m3": [2800, 2850],
        "Viscosidad_Pa_s": [0.5, 0.6],
        "Basicidad_CaO_SiO2": [1.33, 1.09],
        # Variable objetivo que termina en _pct (NO es composición)
        "Fraccion_Cristalina_pct": [45.0, 52.0],
    }
    return pd.DataFrame(data)


class TestColumnasComposicion:
    """Tests para la detección de columnas de composición."""

    def test_detecta_columnas_pct_en_primeras_11(self, sample_dataframe):
        """Debe detectar solo las columnas *_pct en las primeras 11 posiciones."""
        columnas = _columnas_composicion(sample_dataframe)
        assert "CaO_pct" in columnas
        assert "SiO2_pct" in columnas
        assert "TiO2_pct" in columnas

    def test_excluye_pct_fuera_de_primeras_11(self, sample_dataframe):
        """NO debe incluir Fraccion_Cristalina_pct (posición > 11)."""
        columnas = _columnas_composicion(sample_dataframe)
        assert "Fraccion_Cristalina_pct" not in columnas

    def test_cantidad_correcta(self, sample_dataframe):
        """Debe detectar exactamente 11 columnas de composición."""
        columnas = _columnas_composicion(sample_dataframe)
        assert len(columnas) == 11

    def test_dataframe_vacio(self):
        """Un DataFrame vacío no tiene columnas de composición."""
        df = pd.DataFrame()
        columnas = _columnas_composicion(df)
        assert columnas == []


class TestDetectarColumnaTemperatura:
    """Tests para la detección de la columna de temperatura."""

    def test_detecta_temperatura_c(self):
        columnas = ["CaO_pct", "SiO2_pct", "Temperatura_C", "Densidad_kg_m3"]
        assert detectar_columna_temperatura(columnas) == "Temperatura_C"

    def test_detecta_temperatura_k(self):
        columnas = ["CaO_pct", "Temperatura_K", "Densidad_kg_m3"]
        assert detectar_columna_temperatura(columnas) == "Temperatura_K"

    def test_sin_temperatura(self):
        columnas = ["CaO_pct", "SiO2_pct", "Densidad_kg_m3"]
        assert detectar_columna_temperatura(columnas) is None

    def test_no_confunde_con_liquidus(self):
        """No debe confundir Temperatura_Liquidus_K con la temperatura de proceso."""
        columnas = ["CaO_pct", "Temperatura_Liquidus_K", "Densidad_kg_m3"]
        assert detectar_columna_temperatura(columnas) is None


class TestObtenerFeatureColumns:
    """Tests para la obtención de features."""

    def test_incluye_composicion_y_temperatura(self, sample_dataframe):
        features = obtener_feature_columns(sample_dataframe)
        assert "CaO_pct" in features
        assert "Temperatura_C" in features

    def test_no_incluye_targets(self, sample_dataframe):
        features = obtener_feature_columns(sample_dataframe)
        assert "Densidad_kg_m3" not in features
        assert "Viscosidad_Pa_s" not in features


class TestObtenerTargetColumns:
    """Tests para la obtención de variables objetivo."""

    def test_incluye_variables_numericas(self, sample_dataframe):
        targets = obtener_target_columns(sample_dataframe)
        assert "Densidad_kg_m3" in targets
        assert "Viscosidad_Pa_s" in targets
        assert "Basicidad_CaO_SiO2" in targets

    def test_incluye_pct_fuera_de_composicion(self, sample_dataframe):
        """Fraccion_Cristalina_pct es target, no composición."""
        targets = obtener_target_columns(sample_dataframe)
        assert "Fraccion_Cristalina_pct" in targets

    def test_excluye_features(self, sample_dataframe):
        targets = obtener_target_columns(sample_dataframe)
        assert "CaO_pct" not in targets
        assert "Temperatura_C" not in targets


class TestEsColumnaNumerica:
    """Tests para la detección de columnas numéricas."""

    def test_columna_float(self):
        df = pd.DataFrame({"col": [1.0, 2.0, 3.0]})
        assert _es_columna_numerica(df, "col") is True

    def test_columna_string(self):
        df = pd.DataFrame({"col": ["a", "b", "c"]})
        assert _es_columna_numerica(df, "col") is False

    def test_columna_inexistente(self):
        df = pd.DataFrame({"col": [1, 2, 3]})
        assert _es_columna_numerica(df, "no_existe") is False

    def test_columna_mixta_con_numeros(self):
        """Una columna con algunos números se considera numérica."""
        df = pd.DataFrame({"col": [1, None, 3]})
        assert _es_columna_numerica(df, "col") is True