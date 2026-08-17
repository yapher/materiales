"""
Tests para el endpoint de gráfico densidad vs. temperatura.
"""
import pytest


class TestGraficoDensidadEndpoint:
    """Tests de acceso y validación del endpoint."""

    def test_requiere_login(self, client):
        """/mezclas/grafico_densidad requiere autenticación."""
        response = client.post("/mezclas/grafico_densidad")
        assert response.status_code == 401

    def test_requiere_modelo_entrenado(self, auth_client, sample_mix):
        """Sin modelo entrenado debe dar error controlado."""
        response = auth_client.post(
            "/mezclas/grafico_densidad",
            json={
                "mix": sample_mix,
                "temp_min": 1500,
                "temp_max": 2000,
                "intervalo": 20,
            },
        )
        # 400 porque no hay modelo entrenado (ValueError)
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_mezcla_invalida(self, auth_client):
        """Mezcla que no suma 100% debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_densidad",
            json={
                "mix": [
                    {"elemento": "CaO", "pct": 50.0},
                    {"elemento": "SiO2", "pct": 30.0},
                ],
                "temp_min": 1500,
                "temp_max": 2000,
                "intervalo": 20,
            },
        )
        assert response.status_code == 400

    def test_intervalo_invalido(self, auth_client, sample_mix):
        """Intervalo <= 0 debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_densidad",
            json={
                "mix": sample_mix,
                "temp_min": 1500,
                "temp_max": 2000,
                "intervalo": 0,
            },
        )
        assert response.status_code == 400

    def test_rango_invertido(self, auth_client, sample_mix):
        """temp_max <= temp_min debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_densidad",
            json={
                "mix": sample_mix,
                "temp_min": 2000,
                "temp_max": 1500,
                "intervalo": 20,
            },
        )
        assert response.status_code == 400

    def test_exceso_de_puntos(self, auth_client, sample_mix):
        """Más de 500 puntos debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_densidad",
            json={
                "mix": sample_mix,
                "temp_min": 0,
                "temp_max": 10000,
                "intervalo": 1,
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "excesivo" in data.get("error", "").lower() or "500" in data.get("error", "")


class TestGraficoDensidadHelpers:
    """Tests unitarios de helpers internos."""

    def test_validar_parametros_defaults(self):
        """Parámetros None deben tomar valores por defecto."""
        from services.modeling.grafico import _validar_parametros_rango

        t_min, t_max, intervalo = _validar_parametros_rango(None, None, None)
        assert t_min == 1500
        assert t_max == 2000
        assert intervalo == 20

    def test_validar_parametros_custom(self):
        """Parámetros válidos custom se respetan."""
        from services.modeling.grafico import _validar_parametros_rango

        t_min, t_max, intervalo = _validar_parametros_rango(1000, 1800, 50)
        assert t_min == 1000
        assert t_max == 1800
        assert intervalo == 50

    def test_validar_parametros_intervalo_cero(self):
        """Intervalo 0 debe lanzar ValueError."""
        from services.modeling.grafico import _validar_parametros_rango

        with pytest.raises(ValueError):
            _validar_parametros_rango(1500, 2000, 0)

    def test_validar_parametros_rango_invertido(self):
        """temp_max <= temp_min debe lanzar ValueError."""
        from services.modeling.grafico import _validar_parametros_rango

        with pytest.raises(ValueError):
            _validar_parametros_rango(2000, 1500, 20)

    def test_validar_parametros_temperatura_negativa(self):
        """Temperatura mínima negativa debe lanzar ValueError."""
        from services.modeling.grafico import _validar_parametros_rango

        with pytest.raises(ValueError):
            _validar_parametros_rango(-100, 2000, 20)

    def test_detectar_columna_densidad_sin_modelo(self):
        """Sin modelo, debe devolver None."""
        from services.modeling.grafico import _detectar_columna_densidad
        from services.modeling.state import _modelos

        # Asegurar que no hay modelo
        _modelos["test_user_no_modelo"] = None
        resultado = _detectar_columna_densidad("test_user_no_modelo")
        assert resultado is None

    def test_detectar_columna_densidad_canonica(self):
        """Debe detectar Densidad_kg_m3 con prioridad."""
        from services.modeling.grafico import _detectar_columna_densidad
        from services.modeling.state import _modelos

        _modelos["test_user_den_can"] = {
            "Densidad_kg_m3": {"modelo": None},
            "Otra_densidad_rara": {"modelo": None},
        }
        resultado = _detectar_columna_densidad("test_user_den_can")
        assert resultado == "Densidad_kg_m3"

    def test_detectar_columna_densidad_flexible(self):
        """Debe encontrar variantes del nombre."""
        from services.modeling.grafico import _detectar_columna_densidad
        from services.modeling.state import _modelos

        _modelos["test_user_den_flex"] = {
            "Mi_Densidad_Aparente": {"modelo": None},
            "Viscosidad_Pa_s": {"modelo": None},
        }
        resultado = _detectar_columna_densidad("test_user_den_flex")
        assert resultado == "Mi_Densidad_Aparente"