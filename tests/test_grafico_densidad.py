"""
Tests para el endpoint de gráfico densidad vs. temperatura,
el ajuste de regresión lineal, los puntos de regresión en intervalos
y la extracción de puntos reales con información de fila.
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


class TestRegresionLineal:
    """Tests para el ajuste de regresión lineal densidad vs. temperatura."""

    def test_regresion_lineal_perfecta(self):
        """Una relación exactamente lineal debe dar R² = 1.0."""
        from services.modeling.grafico import _calcular_regresion_lineal

        temps = [1500, 1600, 1700, 1800, 1900, 2000]
        dens = [-0.5 * t + 3000 for t in temps]
        reg = _calcular_regresion_lineal(temps, dens)
        assert reg is not None
        assert abs(reg["pendiente"] - (-0.5)) < 0.001
        assert abs(reg["intercepto"] - 3000) < 0.01
        assert reg["r2"] == 1.0

    def test_regresion_devuelve_linea_con_dos_puntos(self):
        """La recta de regresión debe tener exactamente 2 puntos extremos."""
        from services.modeling.grafico import _calcular_regresion_lineal

        temps = [1500, 1600, 1700]
        dens = [2800, 2780, 2760]
        reg = _calcular_regresion_lineal(temps, dens)
        assert reg is not None
        assert "linea" in reg
        assert len(reg["linea"]) == 2
        assert reg["linea"][0]["x"] == 1500
        assert reg["linea"][1]["x"] == 1700

    def test_regresion_menos_de_dos_puntos(self):
        """Con menos de 2 puntos debe devolver None."""
        from services.modeling.grafico import _calcular_regresion_lineal

        assert _calcular_regresion_lineal([1500], [2800]) is None
        assert _calcular_regresion_lineal([], []) is None

    def test_regresion_pendiente_negativa(self):
        """La densidad suele disminuir con la temperatura."""
        from services.modeling.grafico import _calcular_regresion_lineal

        temps = [1500, 1600, 1700, 1800]
        dens = [2900, 2850, 2800, 2750]
        reg = _calcular_regresion_lineal(temps, dens)
        assert reg is not None
        assert reg["pendiente"] < 0

    def test_regresion_cantidad_puntos(self):
        """Debe reportar la cantidad de puntos usados en el ajuste."""
        from services.modeling.grafico import _calcular_regresion_lineal

        temps = [1500, 1600, 1700]
        dens = [2800, 2780, 2760]
        reg = _calcular_regresion_lineal(temps, dens)
        assert reg["cantidad_puntos"] == 3


class TestPuntosRegresionIntervalos:
    """Tests para los puntos cuadrados rojos sobre la regresión."""

    def test_puntos_en_cada_intervalo(self):
        """Debe generar un punto por cada temperatura del intervalo."""
        from services.modeling.grafico import _calcular_puntos_regresion_intervalos

        regresion = {
            "pendiente": -0.5,
            "intercepto": 3000.0,
            "r2": 1.0,
            "linea": [],
            "cantidad_puntos": 26,
        }
        puntos = _calcular_puntos_regresion_intervalos(
            regresion, 1500, 2000, 100
        )
        # (2000 - 1500) / 100 + 1 = 6 puntos
        assert len(puntos) == 6
        assert puntos[0]["temperatura"] == 1500
        assert puntos[-1]["temperatura"] == 2000

    def test_valores_sobre_la_recta(self):
        """Cada punto debe estar sobre la recta y = m*T + b."""
        from services.modeling.grafico import _calcular_puntos_regresion_intervalos

        regresion = {
            "pendiente": -0.5,
            "intercepto": 3000.0,
            "r2": 1.0,
            "linea": [],
            "cantidad_puntos": 6,
        }
        puntos = _calcular_puntos_regresion_intervalos(
            regresion, 1500, 2000, 100
        )
        for p in puntos:
            esperado = -0.5 * p["temperatura"] + 3000.0
            assert abs(p["densidad"] - esperado) < 0.01

    def test_sin_regresion_devuelve_vacio(self):
        """Si no hay regresión, debe devolver lista vacía."""
        from services.modeling.grafico import _calcular_puntos_regresion_intervalos

        puntos = _calcular_puntos_regresion_intervalos(
            None, 1500, 2000, 20
        )
        assert puntos == []

    def test_regresion_sin_pendiente_devuelve_vacio(self):
        """Si la regresión no tiene pendiente, devuelve lista vacía."""
        from services.modeling.grafico import _calcular_puntos_regresion_intervalos

        regresion = {
            "pendiente": None,
            "intercepto": None,
            "r2": None,
            "linea": [],
            "cantidad_puntos": 0,
        }
        puntos = _calcular_puntos_regresion_intervalos(
            regresion, 1500, 2000, 20
        )
        assert puntos == []

    def test_intervalo_pequeno(self):
        """Con intervalo 1 debe generar muchos puntos."""
        from services.modeling.grafico import _calcular_puntos_regresion_intervalos

        regresion = {
            "pendiente": -0.1,
            "intercepto": 2900.0,
            "r2": 0.99,
            "linea": [],
            "cantidad_puntos": 51,
        }
        puntos = _calcular_puntos_regresion_intervalos(
            regresion, 1500, 1550, 10
        )
        # (1550 - 1500) / 10 + 1 = 6 puntos
        assert len(puntos) == 6


class TestPuntosReales:
    """Tests para la extracción de puntos reales con info de fila."""

    def _crear_df(self):
        """
        Crea un DataFrame de prueba con DOS grupos de composición:
        - Grupo A: CaO=25, SiO2=40, MnO=35 (4 temperaturas)
        - Grupo B: CaO=50, SiO2=30, Al2O3=20 (2 temperaturas)
        """
        import pandas as pd
        return pd.DataFrame({
            "CaO_pct": [25, 25, 25, 25, 50, 50],
            "SiO2_pct": [40, 40, 40, 40, 30, 30],
            "Al2O3_pct": [0, 0, 0, 0, 20, 20],
            "MnO_pct": [35, 35, 35, 35, 0, 0],
            "Basicidad_CaO_SiO2": [0.625, 0.625, 0.625, 0.625, 1.67, 1.67],
            "Temperatura_C": [1447, 1487, 1537, 1587, 1500, 1600],
            "Densidad_kg_m3": [3050, 3045, 3015, 3000, 2800, 2750],
        })

    def test_extrae_solo_mismo_grupo(self):
        """Debe extraer solo las filas con la composición exacta del Grupo A."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
            "Al2O3_pct": 0.0,
            "MnO_pct": 35.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) == 4
        temps = [p["temperatura"] for p in puntos]
        assert 1447 in temps
        assert 1487 in temps
        assert 1537 in temps
        assert 1587 in temps
        assert 1500 not in temps
        assert 1600 not in temps

    def test_incluye_info_de_fila(self):
        """Cada punto debe incluir la información completa de la fila."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
            "Al2O3_pct": 0.0,
            "MnO_pct": 35.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) > 0
        primer_punto = puntos[0]
        assert "fila" in primer_punto
        assert "indice_dataset" in primer_punto
        # Verificar que la fila tiene las columnas del dataset
        fila = primer_punto["fila"]
        assert "CaO_pct" in fila
        assert "SiO2_pct" in fila
        assert "MnO_pct" in fila
        assert "Temperatura_C" in fila
        assert "Densidad_kg_m3" in fila
        assert "Basicidad_CaO_SiO2" in fila

    def test_info_fila_valores_correctos(self):
        """Los valores de la fila deben ser correctos."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
            "Al2O3_pct": 0.0,
            "MnO_pct": 35.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        # El primer punto debería ser T=1447, densidad=3050
        primer_punto = puntos[0]
        assert primer_punto["temperatura"] == 1447
        assert primer_punto["densidad"] == 3050
        assert primer_punto["fila"]["CaO_pct"] == 25
        assert primer_punto["fila"]["SiO2_pct"] == 40
        assert primer_punto["fila"]["MnO_pct"] == 35
        assert primer_punto["fila"]["Basicidad_CaO_SiO2"] == 0.625

    def test_no_incluye_otro_grupo(self):
        """No debe incluir filas de otro grupo de composición."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 50.0,
            "SiO2_pct": 30.0,
            "Al2O3_pct": 20.0,
            "MnO_pct": 0.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) == 2
        temps = [p["temperatura"] for p in puntos]
        assert 1500 in temps
        assert 1600 in temps
        assert 1447 not in temps

    def test_ordenado_por_temperatura(self):
        """Los puntos deben estar ordenados por temperatura."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
            "Al2O3_pct": 0.0,
            "MnO_pct": 35.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        temps = [p["temperatura"] for p in puntos]
        assert temps == sorted(temps)

    def test_composicion_inexistente_devuelve_vacio(self):
        """Si no hay filas con esa composición, devuelve lista vacía."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {
            "CaO_pct": 99.0,
            "SiO2_pct": 1.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert puntos == []

    def test_excluye_densidad_negativa(self):
        """Las densidades <= 0 deben excluirse."""
        import pandas as pd
        from services.modeling.grafico import _extraer_puntos_reales

        df = pd.DataFrame({
            "CaO_pct": [25, 25],
            "SiO2_pct": [40, 40],
            "Temperatura_C": [1447, 1487],
            "Densidad_kg_m3": [3050, -5.0],
        })
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) == 1
        assert puntos[0]["densidad"] == 3050

    def test_columna_densidad_inexistente(self):
        """Si la columna de densidad no existe, devuelve lista vacía."""
        from services.modeling.grafico import _extraer_puntos_reales

        df = self._crear_df()
        composicion_esperada = {"CaO_pct": 25.0}
        puntos = _extraer_puntos_reales(
            df,
            "Columna_Inexistente",
            composicion_esperada,
        )
        assert puntos == []

    def test_dataframe_vacio(self):
        """Un DataFrame vacío debe devolver lista vacía."""
        import pandas as pd
        from services.modeling.grafico import _extraer_puntos_reales

        df = pd.DataFrame()
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            {"CaO_pct": 25.0},
        )
        assert puntos == []

    def test_sin_columna_temperatura(self):
        """Si no hay columna de temperatura, devuelve lista vacía."""
        import pandas as pd
        from services.modeling.grafico import _extraer_puntos_reales

        df = pd.DataFrame({
            "CaO_pct": [25, 25],
            "Densidad_kg_m3": [2800, 2850],
        })
        composicion_esperada = {"CaO_pct": 25.0}
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert puntos == []

    def test_tolerancia_en_composicion(self):
        """Valores dentro de la tolerancia deben coincidir."""
        import pandas as pd
        from services.modeling.grafico import _extraer_puntos_reales

        df = pd.DataFrame({
            "CaO_pct": [25.3, 25.0],
            "SiO2_pct": [40.0, 40.0],
            "Temperatura_C": [1447, 1487],
            "Densidad_kg_m3": [3050, 3045],
        })
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) == 2

    def test_fuera_de_tolerancia_no_coincide(self):
        """Valores fuera de la tolerancia NO deben coincidir."""
        import pandas as pd
        from services.modeling.grafico import _extraer_puntos_reales

        df = pd.DataFrame({
            "CaO_pct": [26.0, 25.0],
            "SiO2_pct": [40.0, 40.0],
            "Temperatura_C": [1447, 1487],
            "Densidad_kg_m3": [3050, 3045],
        })
        composicion_esperada = {
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
        }
        puntos = _extraer_puntos_reales(
            df,
            "Densidad_kg_m3",
            composicion_esperada,
        )
        assert len(puntos) == 1
        assert puntos[0]["temperatura"] == 1487


class TestFilaADictSeguro:
    """Tests para la conversión de filas a dict JSON-safe."""

    def test_fila_con_valores_numericos(self):
        """Debe convertir valores numéricos correctamente."""
        import pandas as pd
        from services.modeling.grafico import _fila_a_dict_seguro

        fila = pd.Series({
            "CaO_pct": 25.0,
            "SiO2_pct": 40.0,
            "Temperatura_C": 1447,
            "Densidad_kg_m3": 3050.123456,
        })
        resultado = _fila_a_dict_seguro(fila, list(fila.index))
        assert resultado["CaO_pct"] == 25.0
        assert resultado["SiO2_pct"] == 40.0
        assert resultado["Temperatura_C"] == 1447
        assert resultado["Densidad_kg_m3"] == 3050.1235  # redondeado a 4 decimales

    def test_fila_con_nan(self):
        """Los valores NaN deben convertirse a None."""
        import pandas as pd
        import numpy as np
        from services.modeling.grafico import _fila_a_dict_seguro

        fila = pd.Series({
            "CaO_pct": 25.0,
            "SiO2_pct": np.nan,
        })
        resultado = _fila_a_dict_seguro(fila, list(fila.index))
        assert resultado["CaO_pct"] == 25.0
        assert resultado["SiO2_pct"] is None

    def test_fila_con_string(self):
        """Los valores string deben mantenerse como string."""
        import pandas as pd
        from services.modeling.grafico import _fila_a_dict_seguro

        fila = pd.Series({
            "nombre": "muestra_1",
            "valor": 42,
        })
        resultado = _fila_a_dict_seguro(fila, list(fila.index))
        assert resultado["nombre"] == "muestra_1"
        assert resultado["valor"] == 42

    def test_columna_inexistente(self):
        """Una columna que no está en la fila debe dar None."""
        import pandas as pd
        from services.modeling.grafico import _fila_a_dict_seguro

        fila = pd.Series({"CaO_pct": 25.0})
        resultado = _fila_a_dict_seguro(fila, ["CaO_pct", "Columna_Faltante"])
        assert resultado["CaO_pct"] == 25.0
        assert resultado["Columna_Faltante"] is None