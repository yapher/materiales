"""
Rutas de la página de inicio.
"""

from flask import render_template


def register(bp):
    """
    Registra las rutas de la página de inicio sobre el blueprint de home.
    """

    @bp.route("/")
    @bp.route("/inicio")
    def index():
        return render_template("home/index.html")