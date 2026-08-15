from flask import (
    Blueprint,
    render_template,
    request,
    jsonify,
    send_file,
)

from services.excel_service import (
    cargar_excel_service,
    guardar_prediccion_en_dataset,
    listar_filas_usuario,
    eliminar_fila_usuario,
    obtener_fila_usuario,
    actualizar_fila_usuario,
)

from services.pdf_service import generar_pdf_prediccion, generar_pdf_fila_dataset

from services.mezcla_service import (
    ELEMENTOS,
    iniciar_entrenamiento,
    obtener_estado_entrenamiento,
    predecir_service,
    estado_service,
    guardar_ultima_prediccion,
    obtener_ultima_prediccion,
)

from services.constants import (
    VARIABLES_ENTRENABLES,
    VARIABLE_ENTRENABLE_POR_DEFECTO,
)

from utils import manejar_errores_json, login_required, login_required_json, usuario_actual


mezclas_bp = Blueprint("mezclas", __name__)


@mezclas_bp.route("/mezclas")
@login_required
def index():
    return render_template(
        "index.html",
        elementos=ELEMENTOS,
        variables_entrenables=VARIABLES_ENTRENABLES,
        variable_entrenable_default=VARIABLE_ENTRENABLE_POR_DEFECTO,
    )


@mezclas_bp.route("/mezclas/cargar_dataset", methods=["POST"])
@login_required_json
@manejar_errores_json
def cargar_dataset():
    info = cargar_excel_service()
    return jsonify({
        "filas": info["filas"],
        "columnas": info["columnas"],
        "mensaje": "Dataset listo",
    })


@mezclas_bp.route("/mezclas/entrenar", methods=["POST"])
@login_required_json
@manejar_errores_json
def entrenar():
    data = request.get_json(silent=True) or {}
    variables = data.get("variables")

    iniciado = iniciar_entrenamiento(targets=variables)

    if not iniciado:
        return jsonify({
            "error": "Ya hay un entrenamiento en curso para tu usuario"
        }), 409

    return jsonify({
        "ok": True,
        "mensaje": "Entrenamiento iniciado",
        "variables_solicitadas": variables,
    })


@mezclas_bp.route("/mezclas/entrenar/estado")
@login_required_json
@manejar_errores_json
def entrenar_estado():
    return jsonify(obtener_estado_entrenamiento())


@mezclas_bp.route("/mezclas/estado")
@login_required_json
@manejar_errores_json
def estado():
    return jsonify(estado_service())


@mezclas_bp.route("/mezclas/predecir", methods=["POST"])
@login_required_json
@manejar_errores_json
def predecir():
    data = request.get_json()
    mix = data.get("mix", [])
    temperatura = data.get("temperatura")
    resultado = predecir_service(mix, temperatura)
    guardar_ultima_prediccion(mix, temperatura, resultado)
    return jsonify({"tabla_prediccion": resultado})


@mezclas_bp.route("/mezclas/ultima_prediccion")
@login_required_json
@manejar_errores_json
def ultima_prediccion():
    datos = obtener_ultima_prediccion()
    return jsonify(datos or {})


@mezclas_bp.route("/mezclas/guardar_prediccion", methods=["POST"])
@login_required_json
@manejar_errores_json
def guardar_prediccion():
    data = request.get_json()
    mix = data.get("mix", [])
    temperatura = data.get("temperatura")
    tabla = predecir_service(mix, temperatura)
    resultado = guardar_prediccion_en_dataset(mix, temperatura, tabla)
    return jsonify({
        "ok": True,
        "mensaje": (
            f"Predicción guardada en tu dataset ({resultado['filas']} filas ahora). "
            "Reentrená el modelo para que la tenga en cuenta."
        ),
    })


@mezclas_bp.route("/mezclas/predecir/pdf", methods=["POST"])
@login_required_json
@manejar_errores_json
def predecir_pdf():
    data = request.get_json()
    mix = data.get("mix", [])
    temperatura = data.get("temperatura")
    tabla = predecir_service(mix, temperatura)
    usuario = usuario_actual()
    buffer = generar_pdf_prediccion(
        mix, temperatura, tabla,
        usuario=usuario["username"] if usuario else None,
    )
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name="prediccion_mezcla.pdf",
    )


@mezclas_bp.route("/mezclas/dataset")
@login_required
def dataset_view():
    return render_template("mi_dataset.html")


@mezclas_bp.route("/mezclas/dataset/filas")
@login_required_json
@manejar_errores_json
def dataset_filas():
    return jsonify(listar_filas_usuario())


@mezclas_bp.route("/mezclas/dataset/filas/<int:indice>", methods=["PUT"])
@login_required_json
@manejar_errores_json
def dataset_editar_fila(indice):
    valores = request.get_json() or {}
    actualizar_fila_usuario(indice, valores)
    return jsonify({"ok": True, "mensaje": "Fila actualizada"})


@mezclas_bp.route("/mezclas/dataset/filas/<int:indice>", methods=["DELETE"])
@login_required_json
@manejar_errores_json
def dataset_borrar_fila(indice):
    eliminar_fila_usuario(indice)
    return jsonify({
        "ok": True,
        "mensaje": "Fila eliminada de tu dataset. Reentrená el modelo si ya lo habías entrenado con ella.",
    })


@mezclas_bp.route("/mezclas/dataset/filas/<int:indice>/pdf")
@login_required
@manejar_errores_json
def dataset_fila_pdf(indice):
    columnas, fila = obtener_fila_usuario(indice)
    usuario = usuario_actual()
    buffer = generar_pdf_fila_dataset(
        "Fila de mi dataset",
        indice,
        columnas,
        fila["valores"],
        inconsistente=fila["inconsistente"],
        motivo=fila["motivo"],
        generado_para=usuario["username"] if usuario else None,
    )
    return send_file(
        buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"fila_dataset_{indice}.pdf",
    )