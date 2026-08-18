"""
Tests de verificación de modularización y ausencia de código muerto.
Verifica que los archivos monolíticos duplicados no existan y que
los paquetes modulares estén correctamente estructurados.
"""
import os
import pytest
from pathlib import Path

# Directorio raíz del proyecto
RAIZ = Path(__file__).resolve().parent.parent


class TestCodigoMuerto:
    """Verifica que archivos duplicados/muertos fueron eliminados."""

    def test_no_existe_grafico_densidad_monolitico_js(self):
        """El JS monolítico de grafico_densidad debe estar eliminado."""
        ruta = RAIZ / "static" / "js" / "grafico_densidad.js"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: está duplicado por "
            f"static/js/grafico_densidad/ (modular)"
        )

    def test_no_existe_grafico_py_monolitico(self):
        """El módulo monolítico services/modeling/grafico.py debe eliminarse."""
        ruta = RAIZ / "services" / "modeling" / "grafico.py"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: está duplicado por "
            f"services/modeling/grafico/ (paquete)"
        )

    def test_no_existe_diagnostico_py_monolitico(self):
        """El módulo monolítico blueprints/diagnostico.py debe eliminarse."""
        ruta = RAIZ / "blueprints" / "diagnostico.py"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: está duplicado por "
            f"blueprints/diagnostico/ (paquete)"
        )

    def test_no_existe_base_scripts(self):
        """base_scripts.html no se usa (reemplazado por scripts.html)."""
        ruta = (
            RAIZ / "templates" / "partials" / "layout" / "base_scripts.html"
        )
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: no es usado por base.html"
        )

    def test_no_existe_modal_grafico_densidad(self):
        """El modal de gráfico densidad fue reemplazado por panel inline."""
        ruta = (
            RAIZ / "templates" / "partials" / "mezclas"
            / "modal_grafico_densidad.html"
        )
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: reemplazado por "
            f"partials/grafico_densidad/panel.html"
        )

    def test_no_existe_panel_grafico_densidad_inline_mezclas(self):
        """El panel inline viejo en mezclas/ fue reemplazado."""
        ruta = (
            RAIZ / "templates" / "partials" / "mezclas"
            / "panel_grafico_densidad_inline.html"
        )
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: reemplazado por "
            f"partials/grafico_densidad/panel.html"
        )

    def test_no_existe_mi_dataset_tabla(self):
        """Ya no existen datasets personales."""
        ruta = (
            RAIZ / "templates" / "partials" / "dataset"
            / "mi_dataset_tabla.html"
        )
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: ya no hay datasets personales"
        )

    def test_no_existe_modal_inconsistencia_mi_dataset(self):
        """Ya no existen datasets personales."""
        ruta = (
            RAIZ / "templates" / "partials" / "dataset"
            / "modal_inconsistencia_mi_dataset.html"
        )
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: ya no hay datasets personales"
        )

    def test_no_existe_css_grafico_densidad_raiz(self):
        """El CSS duplicado en raíz debe eliminarse."""
        ruta = RAIZ / "static" / "css" / "grafico_densidad.css"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: duplicado de "
            f"features/grafico_densidad.css"
        )

    def test_no_existe_css_futuro(self):
        """futuro.css no se carga en ningún template."""
        ruta = RAIZ / "static" / "css" / "futuro.css"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: no se carga en ningún template"
        )

    def test_no_existe_grafico_tarta_monolitico(self):
        """El JS monolítico de grafico_tarta debe estar eliminado."""
        ruta = RAIZ / "static" / "js" / "grafico_tarta.js"
        assert not ruta.exists(), (
            f"{ruta} debe eliminarse: está modularizado en "
            f"static/js/grafico_tarta/"
        )


class TestEstructuraModular:
    """Verifica que los módulos existen con la estructura correcta."""

    def test_modulos_grafico_densidad_js(self):
        """El directorio grafico_densidad/ tiene los 9 módulos."""
        dir_modulos = RAIZ / "static" / "js" / "grafico_densidad"
        assert dir_modulos.is_dir()
        esperados = [
            "00-namespace.js",
            "01-helpers.js",
            "02-filtros.js",
            "03-composicion.js",
            "04-stats.js",
            "05-grafico.js",
            "06-backend.js",
            "07-exportar.js",
            "08-init.js",
        ]
        for archivo in esperados:
            ruta = dir_modulos / archivo
            assert ruta.exists(), f"Falta {ruta}"

    def test_modulos_mezclas_js(self):
        """El directorio mezclas/ tiene los 12 módulos."""
        dir_modulos = RAIZ / "static" / "js" / "mezclas"
        assert dir_modulos.is_dir()
        esperados = [
            "00-namespace.js",
            "01-format.js",
            "02-ui.js",
            "03-state.js",
            "04-temperatura.js",
            "05-visibilidad.js",
            "06-tablas.js",
            "07-mezcla-ui.js",
            "08-composicion.js",
            "09-entrenamiento.js",
            "10-prediccion.js",
            "11-init.js",
        ]
        for archivo in esperados:
            ruta = dir_modulos / archivo
            assert ruta.exists(), f"Falta {ruta}"

    def test_modulos_grafico_tarta_js(self):
        """El directorio grafico_tarta/ tiene los 7 módulos."""
        dir_modulos = RAIZ / "static" / "js" / "grafico_tarta"
        assert dir_modulos.is_dir()
        esperados = [
            "00-namespace.js",
            "01-helpers.js",
            "02-construccion.js",
            "03-render.js",
            "04-animacion.js",
            "05-interaccion.js",
            "06-init.js",
        ]
        for archivo in esperados:
            ruta = dir_modulos / archivo
            assert ruta.exists(), f"Falta {ruta}"

    def test_paquete_grafico_modeling(self):
        """El paquete services/modeling/grafico/ tiene los módulos."""
        dir_modulos = RAIZ / "services" / "modeling" / "grafico"
        assert dir_modulos.is_dir()
        esperados = [
            "__init__.py",
            "parametros.py",
            "densidad.py",
            "regresion.py",
            "reales.py",
            "principal.py",
        ]
        for archivo in esperados:
            ruta = dir_modulos / archivo
            assert ruta.exists(), f"Falta {ruta}"

    def test_paquete_diagnostico_blueprint(self):
        """El paquete blueprints/diagnostico/ existe."""
        dir_modulos = RAIZ / "blueprints" / "diagnostico"
        assert dir_modulos.is_dir()
        assert (dir_modulos / "__init__.py").exists()
        assert (dir_modulos / "routes_analisis.py").exists()


class TestCSSFacades:
    """Verifica que los CSS de raíz sean fachadas con @import."""

    def test_configuracion_entrenamiento_es_fachada(self):
        """configuracion_entrenamiento.css debe ser un @import."""
        ruta = (
            RAIZ / "static" / "css"
            / "configuracion_entrenamiento.css"
        )
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        assert "@import" in contenido, (
            "configuracion_entrenamiento.css debe ser una fachada "
            "con @import, no contener estilos duplicados"
        )
        assert "features/configuracion_entrenamiento.css" in contenido

    def test_flujo_es_fachada(self):
        """flujo.css debe ser un @import."""
        ruta = RAIZ / "static" / "css" / "flujo.css"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        assert "@import" in contenido

    def test_mezclas_es_fachada(self):
        """mezclas.css debe ser un @import."""
        ruta = RAIZ / "static" / "css" / "mezclas.css"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        assert "@import" in contenido

    def test_grafico_tarta_es_fachada(self):
        """grafico_tarta.css debe ser un @import."""
        ruta = RAIZ / "static" / "css" / "grafico_tarta.css"
        assert ruta.exists()
        contenido = ruta.read_text(encoding="utf-8")
        assert "@import" in contenido


class TestTemplatesActivos:
    """Verifica que los templates activos sean los correctos."""

    def test_base_html_usa_scripts(self):
        """base.html debe incluir scripts.html, no base_scripts.html."""
        ruta = RAIZ / "templates" / "base.html"
        contenido = ruta.read_text(encoding="utf-8")
        assert "scripts.html" in contenido
        assert "base_scripts.html" not in contenido

    def test_index_html_usa_panel_grafico_densidad(self):
        """index.html debe incluir el panel modular de densidad."""
        ruta = RAIZ / "templates" / "index.html"
        contenido = ruta.read_text(encoding="utf-8")
        assert "grafico_densidad/panel.html" in contenido

    def test_dataset_html_no_referencia_mi_dataset(self):
        """dataset.html no debe referenciar 'mi dataset'."""
        ruta = RAIZ / "templates" / "dataset.html"
        contenido = ruta.read_text(encoding="utf-8")
        assert "mi_dataset" not in contenido.lower()