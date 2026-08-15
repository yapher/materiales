import logging
from flask import Flask, jsonify

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from config import Config

from blueprints.mezclas import mezclas_bp
from blueprints.home import home_bp
from blueprints.admin import admin_bp
from blueprints.auth import auth_bp
from blueprints.ayuda import ayuda_bp
from blueprints.diagnostico import diagnostico_bp

from services.oauth_service import init_oauth, google_habilitado, x_habilitado

from utils import asegurar_admin_semilla, usuario_actual


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    logging.basicConfig(
        level=logging.DEBUG if app.config["DEBUG"] else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    app.register_blueprint(home_bp)
    app.register_blueprint(mezclas_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(ayuda_bp)
    app.register_blueprint(diagnostico_bp)

    init_oauth(app)

    @app.context_processor
    def inject_usuario_sesion():
        return {"usuario_sesion": usuario_actual()}

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"}), 200

    with app.app_context():
        asegurar_admin_semilla()

    logging.info("--------------------------------------------")
    logging.info("IA Mezclas Industriales lista para recibir requests")
    logging.info(
        "Login social: Google=%s, X=%s",
        "activado" if google_habilitado() else "desactivado",
        "activado" if x_habilitado() else "desactivado",
    )

    if Config.SECRET_KEY_ES_DEFAULT:
        if app.config["DEBUG"]:
            logging.warning(
                "Estás usando la SECRET_KEY de ejemplo. Sirve para "
                "desarrollo local, pero antes de subir a un servidor real "
                "definí la variable de entorno SECRET_KEY con un valor propio."
            )
        else:
            logging.error(
                "PELIGRO: DEBUG está apagado (modo producción) pero la "
                "SECRET_KEY sigue siendo la de ejemplo del código fuente. "
                "Definí la variable de entorno SECRET_KEY con un valor propio. "
                "Sin esto, cualquiera puede falsificar la sesión de cualquier usuario."
            )

    if Config.ADMIN_SEED_PASSWORD == "jazmin112":
        logging.warning(
            "El usuario admin '%s' sigue con la contraseña por defecto. "
            "Cambiala después del primer login si esto va a producción.",
            Config.ADMIN_SEED_USUARIO,
        )

    logging.info("--------------------------------------------")

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=app.config["DEBUG"])