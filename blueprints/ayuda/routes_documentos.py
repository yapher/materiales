"""
Rutas de documentos de ayuda:
- índice de ayuda
- tutorial de uso
- teoría de los modelos
- documentación técnica del sistema (solo admin)
"""

from flask import (
    render_template,
    send_file,
)

from services.ayuda_content import (
    contenido_tutorial,
    contenido_modelos,
    contenido_sistema,
)

from services.pdf_service import generar_pdf_documento

from utils import login_required, admin_required, usuario_actual


def register(bp):
    """
    Registra las rutas de documentos de ayuda sobre el blueprint de ayuda.
    """

    # ==========================================================
    # ÍNDICE DE AYUDA
    # ==========================================================
    @bp.route("/")
    @login_required
    def index():
        return render_template("ayuda/index.html")

    # ==========================================================
    # TUTORIAL DE USO (cualquier usuario logueado)
    # ==========================================================
    @bp.route("/tutorial")
    @login_required
    def tutorial():
        secciones, subtitulo = contenido_tutorial()

        return render_template(
            "ayuda/documento.html",
            titulo="Tutorial de uso",
            subtitulo=subtitulo,
            secciones=secciones,
            icono="bi-book",
            pdf_url_endpoint="ayuda.tutorial_pdf",
        )

    @bp.route("/tutorial/pdf")
    @login_required
    def tutorial_pdf():
        secciones, subtitulo = contenido_tutorial()

        buffer = generar_pdf_documento(
            "Tutorial de uso",
            secciones,
            subtitulo=subtitulo
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="tutorial_ia_mezclas.pdf",
        )

    # ==========================================================
    # TEORÍA DE LOS MODELOS (cualquier usuario logueado)
    # ==========================================================
    @bp.route("/modelos")
    @login_required
    def modelos():
        secciones, subtitulo = contenido_modelos()

        return render_template(
            "ayuda/documento.html",
            titulo="Teoría de los modelos",
            subtitulo=subtitulo,
            secciones=secciones,
            icono="bi-diagram-3",
            pdf_url_endpoint="ayuda.modelos_pdf",
        )

    @bp.route("/modelos/pdf")
    @login_required
    def modelos_pdf():
        secciones, subtitulo = contenido_modelos()

        buffer = generar_pdf_documento(
            "Teoría de los modelos",
            secciones,
            subtitulo=subtitulo
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="teoria_modelos_ia_mezclas.pdf",
        )

    # ==========================================================
    # DOCUMENTACIÓN TÉCNICA DEL SISTEMA (SOLO ADMIN)
    # ==========================================================
    @bp.route("/sistema")
    @admin_required
    def sistema():
        secciones, subtitulo = contenido_sistema()

        return render_template(
            "ayuda/documento.html",
            titulo="Documentación técnica del sistema",
            subtitulo=subtitulo,
            secciones=secciones,
            icono="bi-code-slash",
            pdf_url_endpoint="ayuda.sistema_pdf",
        )

    @bp.route("/sistema/pdf")
    @admin_required
    def sistema_pdf():
        secciones, subtitulo = contenido_sistema()
        usuario = usuario_actual()

        buffer = generar_pdf_documento(
            "Documentación técnica del sistema",
            secciones,
            subtitulo=subtitulo,
            generado_para=(
                f"Documento confidencial - generado para {usuario['username']}"
            ),
        )

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="documentacion_tecnica_sistema.pdf",
        )