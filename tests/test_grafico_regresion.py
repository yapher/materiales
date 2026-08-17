"""
Tests para el endpoint de gráfico de regresión lineal.
"""
import pytest


class TestGraficoRegresionEndpoint:
    """Tests de acceso y validación del endpoint."""

    def test_variables_requiere_login(self, client):
        """/mezclas/grafico_regresion/variables requiere autenticación."""
        response = client.get("/mezclas/grafico_regresion/variables")
        assert response.status_code == 401

    def test_regresion_requiere_login(self, client):
        """/mezclas/grafico_regresion requiere autenticación."""
        response = client.post("/mezclas/grafico_regresion")
        assert response.status_code == 401

    def test_variables_sin_modelo(self, auth_client):
        """Sin modelo entrenado debe devolver lista vacía."""
        response = auth_client.get("/mezclas/grafico_regresion/variables")
        assert response.status_code == 200
        data = response.get_json()
        assert "variables" in data
        assert isinstance(data["variables"], list)
        assert len(data["variables"]) == 0

    def test_regresion_sin_modelo(self, auth_client):
        """Sin modelo entrenado debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_regresion",
            json={"columna": "Densidad_kg_m3"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "entren" in data["error"].lower()

    def test_regresion_sin_columna(self, auth_client):
        """Sin columna debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_regresion",
            json={},
        )
        assert response.status_code == 400

    def test_regresion_columna_inexistente(self, auth_client):
        """Columna no entrenada debe dar error."""
        response = auth_client.post(
            "/mezclas/grafico_regresion",
            json={"columna": "Variable_Inexistente_XYZ"},
        )
        assert response.status_code == 400


class TestGraficoRegresionHelpers:
    """Tests unitarios de helpers internos."""

    def test_calcular_estadisticas_perfectas(self):
        """Regresión perfecta debe dar R² = 1, pendiente = 1, intercepto = 0."""
        import numpy as np
        from services.modeling.regresion import _calcular_estadisticas_regresion

        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        stats = _calcular_estadisticas_regresion(y_real, y_pred)
        assert stats["r2"] == 1.0
        assert stats["r2_predictivo"] == 1.0
        assert abs(stats["pendiente"] - 1.0) < 0.001
        assert abs(stats["intercepto"]) < 0.001
        assert stats["rmse"] == 0.0
        assert stats["mae"] == 0.0

    def test_calcular_estadisticas_desplazado(self):
        """
        Regresión desplazada (y_pred = y_real + 10).
        El R² del ajuste lineal debe ser 1.0 (relación perfectamente lineal).
        El R² predictivo será negativo (offset grande vs. varianza).
        """
        import numpy as np
        from services.modeling.regresion import _calcular_estadisticas_regresion

        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = y_real + 10.0
        stats = _calcular_estadisticas_regresion(y_real, y_pred)
        # R² del fit (correlación²) debe ser 1.0: relación perfectamente lineal
        assert stats["r2"] == 1.0
        # Pendiente debe ser 1.0
        assert abs(stats["pendiente"] - 1.0) < 0.001
        # Intercepto debe ser 10.0
        assert abs(stats["intercepto"] - 10.0) < 0.001
        # MAE debe ser 10.0 (offset constante)
        assert stats["mae"] == 10.0
        # R² predictivo será negativo (offset > varianza de datos)
        assert stats["r2_predictivo"] is not None
        assert stats["r2_predictivo"] < 0

    def test_calcular_estadisticas_mal_ajuste(self):
        """
        Regresión con relación inversa perfecta.
        El R² del fit debe ser 1.0 (correlación = -1, al cuadrado = 1).
        El R² predictivo debe ser negativo (peor que la media).
        """
        import numpy as np
        from services.modeling.regresion import _calcular_estadisticas_regresion

        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([5.0, 4.0, 3.0, 2.0, 1.0])  # inverso
        stats = _calcular_estadisticas_regresion(y_real, y_pred)
        # R² del fit = 1.0 porque hay relación lineal perfecta (inversa)
        assert stats["r2"] == 1.0
        # R² predictivo debe ser negativo
        assert stats["r2_predictivo"] is not None
        assert stats["r2_predictivo"] <= 0
        # Pendiente debe ser -1.0
        assert abs(stats["pendiente"] - (-1.0)) < 0.001

    def test_calcular_estadisticas_un_punto(self):
        """Con menos de 2 puntos debe devolver None."""
        import numpy as np
        from services.modeling.regresion import _calcular_estadisticas_regresion

        y_real = np.array([1.0])
        y_pred = np.array([2.0])
        stats = _calcular_estadisticas_regresion(y_real, y_pred)
        assert stats["pendiente"] is None
        assert stats["r2"] is None
        assert stats["cantidad"] == 1

    def test_detectar_outliers_sin_outliers(self):
        """Sin outliers todos los puntos deben quedar dentro del umbral."""
        import numpy as np
        from services.modeling.regresion import _detectar_outliers

        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        y_pred = np.array([1.1, 2.1, 2.9, 4.1, 4.9])
        mascara, umbral, mediana = _detectar_outliers(y_real, y_pred)
        assert mascara.sum() == 0

    def test_detectar_outliers_con_outliers(self):
        """Con un outlier claro debe marcarlo."""
        import numpy as np
        from services.modeling.regresion import _detectar_outliers

        y_real = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        y_pred = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 100.0])
        mascara, umbral, mediana = _detectar_outliers(y_real, y_pred)
        assert mascara.sum() >= 1
        # Usar bool() porque numpy devuelve np.True_ que no es `True` de Python
        assert bool(mascara[5]) is True

    def test_listar_variables_sin_modelo(self):
        """Sin modelo debe devolver lista vacía."""
        from services.modeling.regresion import listar_variables_regresion
        from services.modeling.state import _modelos

        _modelos["test_user_no_modelo_reg"] = None
        resultado = listar_variables_regresion(user_id="test_user_no_modelo_reg")
        assert isinstance(resultado, list)
        assert len(resultado) == 0

    def test_listar_variables_con_modelo(self):
        """Con modelo debe listar las columnas entrenadas."""
        from services.modeling.regresion import listar_variables_regresion
        from services.modeling.state import _modelos

        _modelos["test_user_con_modelo_reg"] = {
            "Densidad_kg_m3": {"modelo": None, "algoritmo": "RandomForest"},
            "Viscosidad_Pa_s": {"modelo": None, "algoritmo": "ExtraTrees"},
        }
        resultado = listar_variables_regresion(user_id="test_user_con_modelo_reg")
        assert len(resultado) == 2
        valores = [v["valor"] for v in resultado]
        assert "Densidad_kg_m3" in valores
        assert "Viscosidad_Pa_s" in valores