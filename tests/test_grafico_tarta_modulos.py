"""
Tests de la modularización del gráfico de tarta 3D.
Verifica que los módulos JS existan y tengan contenido válido.
"""
import pytest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


class TestModulosGraficoTarta:
    """Verifica la estructura modular del gráfico de tarta."""

    def _leer_modulo(self, nombre):
        ruta = (
            RAIZ / "static" / "js" / "grafico_tarta" / nombre
        )
        assert ruta.exists(), f"No existe {ruta}"
        return ruta.read_text(encoding="utf-8")

    def test_namespace_define_objeto_global(self):
        """00-namespace.js debe definir window.GraficoTarta."""
        contenido = self._leer_modulo("00-namespace.js")
        assert "window.GraficoTarta" in contenido
        assert "CONFIG" in contenido
        assert "COLORES_DEFAULT" in contenido

    def test_helpers_define_funciones_basicas(self):
        """01-helpers.js debe definir crear, punto, formatear."""
        contenido = self._leer_modulo("01-helpers.js")
        assert "GT.crear" in contenido
        assert "GT.punto" in contenido
        assert "GT.formatearNumero" in contenido

    def test_construccion_define_svg(self):
        """02-construccion.js debe definir la construcción del SVG."""
        contenido = self._leer_modulo("02-construccion.js")
        assert "GT.construir" in contenido
        assert "GT.asegurarGradientes" in contenido

    def test_render_define_dibujo(self):
        """03-render.js debe definir render y caminoTapa."""
        contenido = self._leer_modulo("03-render.js")
        assert "GT.render" in contenido
        assert "GT.caminoTapa" in contenido
        assert "GT.caminoPared" in contenido

    def test_animacion_define_transicion(self):
        """04-animacion.js debe definir animarHacia."""
        contenido = self._leer_modulo("04-animacion.js")
        assert "GT.animarHacia" in contenido
        assert "requestAnimationFrame" in contenido

    def test_interaccion_define_eventos(self):
        """05-interaccion.js debe definir hover y tooltip."""
        contenido = self._leer_modulo("05-interaccion.js")
        assert "GT.conectarEventos" in contenido
        assert "GT.activarSlice" in contenido
        assert "GT.mostrarTooltip" in contenido
        assert "GT.initToggleTarta" in contenido

    def test_init_define_api_publica(self):
        """06-init.js debe definir la API pública actualizar."""
        contenido = self._leer_modulo("06-init.js")
        assert "GT.actualizar" in contenido
        assert "DOMContentLoaded" in contenido

    def test_no_hay_codigo_duplicado_entre_modulos(self):
        """Cada función debe estar en UN solo módulo."""
        funciones = {
            "GT.render": "03-render.js",
            "GT.animarHacia": "04-animacion.js",
            "GT.conectarEventos": "05-interaccion.js",
            "GT.construir": "02-construccion.js",
        }
        for funcion, modulo_esperado in funciones.items():
            encontrado_en = []
            for i in range(7):
                nombre = f"0{i}-{self._get_nombre(i)}.js"
                try:
                    contenido = self._leer_modulo(nombre)
                    if f"{funcion} = function" in contenido or \
                       f"{funcion} =" in contenido:
                        encontrado_en.append(nombre)
                except (AssertionError, FileNotFoundError):
                    pass
            assert len(encontrado_en) <= 1, (
                f"{funcion} está definido en múltiples módulos: "
                f"{encontrado_en}"
            )

    def _get_nombre(self, indice):
        nombres = [
            "namespace",
            "helpers",
            "construccion",
            "render",
            "animacion",
            "interaccion",
            "init",
        ]
        return nombres[indice]