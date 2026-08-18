"""
Rutas de administración del dataset maestro.
Ahora redirige a la vista unificada de /mezclas/dataset.
Se mantiene el endpoint /admin/dataset por compatibilidad.
"""
from flask import (
    redirect,
    url_for,
)
from utils import admin_required


def register(bp):
    """
    Registra las rutas del dataset maestro sobre el blueprint de admin.
    """

    @bp.route("/dataset")
    @admin_required
    def dataset():
        """
        Redirige a la vista unificada del dataset.
        """
        return redirect(url_for("mezclas.dataset_view"))