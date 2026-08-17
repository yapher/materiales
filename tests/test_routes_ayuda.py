"""
Tests para las rutas del módulo de ayuda.
Verifica acceso, restricciones y contenido.
"""

import pytest


class TestAyudaRoutes:
    """Tests para las rutas de ayuda."""

    def test_ayuda_index_requiere_login(self, client):
        """El índice de ayuda requiere autenticación."""
        response = client.get("/ayuda/", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_ayuda_index_con_sesion(self, auth_client):
        """El índice de ayuda con sesión debe devolver 200."""
        response = auth_client.get("/ayuda/")
        assert response.status_code == 200

    def test_ayuda_index_contiene_titulo(self, auth_client):
        """El índice debe contener el título 'Ayuda'."""
        response = auth_client.get("/ayuda/")
        assert b"Ayuda" in response.data

    def test_ayuda_index_muestra_tutorial(self, auth_client):
        """El índice debe mostrar el enlace al tutorial."""
        response = auth_client.get("/ayuda/")
        assert b"Tutorial de uso" in response.data

    def test_ayuda_index_muestra_modelos(self, auth_client):
        """El índice debe mostrar el enlace a teoría de modelos."""
        response = auth_client.get("/ayuda/")
        assert b"Teor" in response.data

    def test_ayuda_index_no_muestra_sistema_a_usuario_normal(self, auth_client):
        """Un usuario normal NO debe ver la documentación del sistema."""
        response = auth_client.get("/ayuda/")
        assert b"Documentaci" not in response.data or b"sistema" not in response.data


class TestAyudaTutorial:
    """Tests para el tutorial de uso."""

    def test_tutorial_requiere_login(self, client):
        """El tutorial requiere autenticación."""
        response = client.get("/ayuda/tutorial", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_tutorial_con_sesion(self, auth_client):
        """El tutorial con sesión debe devolver 200."""
        response = auth_client.get("/ayuda/tutorial")
        assert response.status_code == 200

    def test_tutorial_contiene_secciones(self, auth_client):
        """El tutorial debe contener secciones relevantes."""
        response = auth_client.get("/ayuda/tutorial")
        assert b"Crear una cuenta" in response.data
        assert b"Entrenar" in response.data
        assert b"mezcla" in response.data

    def test_tutorial_menciona_flujo(self, auth_client):
        """El tutorial debe mencionar el flujo de 3 pasos."""
        response = auth_client.get("/ayuda/tutorial")
        assert b"Paso 1" in response.data or b"flujo" in response.data

    def test_tutorial_menciona_diagnostico(self, auth_client):
        """El tutorial debe mencionar el panel de diagnóstico."""
        response = auth_client.get("/ayuda/tutorial")
        assert b"diagn" in response.data.lower()

    def test_tutorial_pdf_requiere_login(self, client):
        """El PDF del tutorial requiere autenticación."""
        response = client.get("/ayuda/tutorial/pdf", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_tutorial_pdf_con_sesion(self, auth_client):
        """El PDF del tutorial con sesión debe devolver 200."""
        response = auth_client.get("/ayuda/tutorial/pdf")
        assert response.status_code == 200
        assert response.content_type == "application/pdf"


class TestAyudaModelos:
    """Tests para la teoría de modelos."""

    def test_modelos_requiere_login(self, client):
        """La teoría de modelos requiere autenticación."""
        response = client.get("/ayuda/modelos", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_modelos_con_sesion(self, auth_client):
        """La teoría de modelos con sesión debe devolver 200."""
        response = auth_client.get("/ayuda/modelos")
        assert response.status_code == 200

    def test_modelos_menciona_algoritmos(self, auth_client):
        """Debe mencionar los algoritmos de ML."""
        response = auth_client.get("/ayuda/modelos")
        assert b"RandomForest" in response.data
        assert b"GradientBoosting" in response.data

    def test_modelos_menciona_kfold(self, auth_client):
        """Debe mencionar la validación cruzada."""
        response = auth_client.get("/ayuda/modelos")
        assert b"K-Fold" in response.data or b"validaci" in response.data

    def test_modelos_menciona_outliers(self, auth_client):
        """Debe mencionar el filtro de outliers."""
        response = auth_client.get("/ayuda/modelos")
        assert b"outlier" in response.data.lower()

    def test_modelos_pdf_con_sesion(self, auth_client):
        """El PDF de modelos con sesión debe devolver 200."""
        response = auth_client.get("/ayuda/modelos/pdf")
        assert response.status_code == 200
        assert response.content_type == "application/pdf"


class TestAyudaSistema:
    """Tests para la documentación técnica del sistema."""

    def test_sistema_requiere_login(self, client):
        """La doc del sistema requiere autenticación."""
        response = client.get("/ayuda/sistema", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_sistema_no_accesible_para_usuario_normal(self, auth_client):
        """Un usuario normal NO puede acceder a la doc del sistema."""
        response = auth_client.get("/ayuda/sistema", follow_redirects=False)
        # Redirige porque no es admin
        assert response.status_code in (301, 302, 308)

    def test_sistema_accesible_para_admin(self, admin_client):
        """Un admin puede acceder a la doc del sistema."""
        response = admin_client.get("/ayuda/sistema")
        assert response.status_code == 200

    def test_sistema_menciona_arquitectura(self, admin_client):
        """Debe mencionar la arquitectura modular."""
        response = admin_client.get("/ayuda/sistema")
        assert b"blueprint" in response.data.lower()

    def test_sistema_menciona_polling(self, admin_client):
        """Debe mencionar el polling (no SSE)."""
        response = admin_client.get("/ayuda/sistema")
        assert b"polling" in response.data.lower()

    def test_sistema_no_menciona_sse(self, admin_client):
        """NO debe mencionar SSE/EventSource (ya no se usa)."""
        response = admin_client.get("/ayuda/sistema")
        assert b"EventSource" not in response.data
        assert b"entrenar_stream" not in response.data

    def test_sistema_menciona_modulos_js(self, admin_client):
        """Debe mencionar la modularización de JS."""
        response = admin_client.get("/ayuda/sistema")
        assert b"00-namespace" in response.data or b"modular" in response.data.lower()

    def test_sistema_menciona_perfil(self, admin_client):
        """Debe mencionar el módulo de perfil."""
        response = admin_client.get("/ayuda/sistema")
        assert b"perfil" in response.data.lower()

    def test_sistema_pdf_requiere_admin(self, auth_client):
        """El PDF del sistema no es accesible para usuarios normales."""
        response = auth_client.get("/ayuda/sistema/pdf", follow_redirects=False)
        assert response.status_code in (301, 302, 308)

    def test_sistema_pdf_con_admin(self, admin_client):
        """El PDF del sistema con admin debe devolver 200."""
        response = admin_client.get("/ayuda/sistema/pdf")
        assert response.status_code == 200
        assert response.content_type == "application/pdf"


class TestAyudaContenido:
    """Tests unitarios del contenido de ayuda."""

    def test_contenido_tutorial_devuelve_secciones(self):
        """contenido_tutorial debe devolver lista de secciones."""
        from services.ayuda_content import contenido_tutorial
        secciones, subtitulo = contenido_tutorial()
        assert isinstance(secciones, list)
        assert len(secciones) > 0
        assert isinstance(subtitulo, str)
        assert len(subtitulo) > 0

    def test_contenido_modelos_devuelve_secciones(self):
        """contenido_modelos debe devolver lista de secciones."""
        from services.ayuda_content import contenido_modelos
        secciones, subtitulo = contenido_modelos()
        assert isinstance(secciones, list)
        assert len(secciones) > 0
        assert isinstance(subtitulo, str)

    def test_contenido_sistema_devuelve_secciones(self):
        """contenido_sistema debe devolver lista de secciones."""
        from services.ayuda_content import contenido_sistema
        secciones, subtitulo = contenido_sistema()
        assert isinstance(secciones, list)
        assert len(secciones) > 0
        assert isinstance(subtitulo, str)

    def test_tutorial_tiene_titulos(self):
        """Cada sección del tutorial debe tener título."""
        from services.ayuda_content import contenido_tutorial
        secciones, _ = contenido_tutorial()
        for seccion in secciones:
            assert "titulo" in seccion
            assert len(seccion["titulo"]) > 0

    def test_modelos_tiene_imagenes(self):
        """La sección de modelos debe incluir diagramas."""
        from services.ayuda_content import contenido_modelos
        secciones, _ = contenido_modelos()
        imagenes = [s.get("imagen") for s in secciones if s.get("imagen")]
        assert len(imagenes) >= 3

    def test_sistema_tiene_codigo(self):
        """La doc del sistema debe incluir bloques de código."""
        from services.ayuda_content import contenido_sistema
        secciones, _ = contenido_sistema()
        codigos = [s.get("codigo") for s in secciones if s.get("codigo")]
        assert len(codigos) >= 1

    def test_modelos_menciona_filtro_outliers(self):
        """La teoría debe documentar el filtro de outliers por residuo."""
        from services.ayuda_content import contenido_modelos
        secciones, _ = contenido_modelos()
        texto_completo = " ".join(
            str(s) for s in secciones
        )
        assert "outlier" in texto_completo.lower()
        assert "residuo" in texto_completo.lower()

    def test_sistema_no_menciona_sse(self):
        """La doc del sistema NO debe mencionar SSE."""
        from services.ayuda_content import contenido_sistema
        secciones, _ = contenido_sistema()
        texto_completo = " ".join(
            str(s) for s in secciones
        )
        assert "EventSource" not in texto_completo
        assert "entrenar_stream" not in texto_completo

    def test_sistema_menciona_polling(self):
        """La doc del sistema debe mencionar polling."""
        from services.ayuda_content import contenido_sistema
        secciones, _ = contenido_sistema()
        texto_completo = " ".join(
            str(s) for s in secciones
        )
        assert "polling" in texto_completo.lower()