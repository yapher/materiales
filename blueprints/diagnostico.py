from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
)

from services.diagnostico_service import (
    obtener_variables_diagnostico,
    analizar_variable,
)

from utils import (
    login_required,
    login_required_json,
    manejar_errores_json,
)

diagnostico_bp = Blueprint(
    "diagnostico",
    __name__,
)


@diagnostico_bp.route("/diagnostico")
@login_required
def index():
    variables, variable_default = obtener_variables_diagnostico()

    return render_template(
        "diagnostico.html",
        variables=variables,
        variable_default=variable_default,
    )


@diagnostico_bp.route("/diagnostico/analizar")
@login_required_json
@manejar_errores_json
def analizar():
    variable = request.args.get("variable")

    if not variable:
        raise ValueError("Seleccioná una variable para analizar.")

    data = analizar_variable(variable)

    return jsonify(data)