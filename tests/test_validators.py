"""
Tests unitarios para utils/validators.py.
Estos son tests de lógica pura, sin dependencias externas.
"""

import pytest
from utils.validators import validar_mezcla_100, validar_temperatura


class TestValidarMezcla100:
    """Tests para la validación de que la mezcla suma 100%."""

    def test_mezcla_valida_exacta(self):
        """Una mezcla que suma exactamente 100 debe ser válida."""
        mix = [
            {"elemento": "CaO", "pct": 50.0},
            {"elemento": "SiO2", "pct": 50.0},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is True
        assert abs(total - 100.0) < 0.01

    def test_mezcla_valida_con_decimales(self):
        """Una mezcla con decimales que suma ~100 debe ser válida."""
        mix = [
            {"elemento": "CaO", "pct": 33.33},
            {"elemento": "SiO2", "pct": 33.33},
            {"elemento": "Al2O3", "pct": 33.34},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is True
        assert abs(total - 100.0) <= 0.01

    def test_mezcla_invalida_suma_menos(self):
        """Una mezcla que suma menos de 100 debe ser inválida."""
        mix = [
            {"elemento": "CaO", "pct": 40.0},
            {"elemento": "SiO2", "pct": 30.0},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is False
        assert abs(total - 70.0) < 0.01

    def test_mezcla_invalida_suma_mas(self):
        """Una mezcla que suma más de 100 debe ser inválida."""
        mix = [
            {"elemento": "CaO", "pct": 60.0},
            {"elemento": "SiO2", "pct": 50.0},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is False
        assert abs(total - 110.0) < 0.01

    def test_mezcla_vacia(self):
        """Una mezcla vacía debe ser inválida (suma 0)."""
        mix = []
        valido, total = validar_mezcla_100(mix)
        assert valido is False
        assert total == 0.0

    def test_mezcla_con_valor_invalido(self):
        """Un elemento con pct no numérico se trata como 0."""
        mix = [
            {"elemento": "CaO", "pct": "invalid"},
            {"elemento": "SiO2", "pct": 100.0},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is True
        assert abs(total - 100.0) < 0.01

    def test_mezcla_con_pct_none(self):
        """Un elemento con pct None se trata como 0."""
        mix = [
            {"elemento": "CaO", "pct": None},
            {"elemento": "SiO2", "pct": 100.0},
        ]
        valido, total = validar_mezcla_100(mix)
        assert valido is True

    def test_mezcla_un_solo_elemento_100(self):
        """Un solo elemento al 100% es válido."""
        mix = [{"elemento": "CaO", "pct": 100.0}]
        valido, total = validar_mezcla_100(mix)
        assert valido is True

    def test_tolerancia_personalizada(self):
        """Se puede pasar una tolerancia personalizada."""
        mix = [
            {"elemento": "CaO", "pct": 99.5},
        ]
        # Con tolerancia 0.01, 99.5 no es válido
        valido, _ = validar_mezcla_100(mix, tolerancia=0.01)
        assert valido is False

        # Con tolerancia 1.0, 99.5 sí es válido
        valido, _ = validar_mezcla_100(mix, tolerancia=1.0)
        assert valido is True


class TestValidarTemperatura:
    """Tests para la validación de temperatura."""

    def test_temperatura_valida_entero(self):
        """Un entero es una temperatura válida."""
        valido, valor = validar_temperatura(1500)
        assert valido is True
        assert valor == 1500.0

    def test_temperatura_valida_float(self):
        """Un float es una temperatura válida."""
        valido, valor = validar_temperatura(1500.5)
        assert valido is True
        assert valor == 1500.5

    def test_temperatura_valida_string_numerico(self):
        """Un string numérico se convierte a float."""
        valido, valor = validar_temperatura("1500")
        assert valido is True
        assert valor == 1500.0

    def test_temperatura_invalida_string(self):
        """Un string no numérico es inválido."""
        valido, valor = validar_temperatura("caliente")
        assert valido is False
        assert valor is None

    def test_temperatura_invalida_none(self):
        """None es inválido."""
        valido, valor = validar_temperatura(None)
        assert valido is False
        assert valor is None

    def test_temperatura_cero(self):
        """Cero es un valor numérico válido (aunque físicamente improbable)."""
        valido, valor = validar_temperatura(0)
        assert valido is True
        assert valor == 0.0

    def test_temperatura_negativa(self):
        """Un valor negativo es numéricamente válido."""
        valido, valor = validar_temperatura(-10)
        assert valido is True
        assert valor == -10.0