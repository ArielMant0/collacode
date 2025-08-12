import config
from dotenv import dotenv_values
from app import bp as main_bp
from app.extensions import login_manager
from flask import Flask, Request
from flask_cors import CORS


class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super(CustomRequest, self).__init__(*args, **kwargs)
        self.max_form_parts = 10


def create_app():
    app = Flask(__name__)
    app.request_class = CustomRequest
    app.secret_key = config.SECRET_KEY
    app.config.update(
        DEBUG=config.DEBUG,
        SECRET_KEY=config.SECRET_KEY,
        MAX_CONTENT_LENGTH=config.MAX_CONTENT_LENGTH,
        SESSION_COOKIE_DOMAIN=config.SESSION_COOKIE_DOMAIN,
        REMEMBER_COOKIE_DOMAIN=config.REMEMBER_COOKIE_DOMAIN,
        REMEMBER_COOKIE_PATH=config.REMEMBER_COOKIE_PATH,
        REMEMBER_COOKIE_SECURE=config.REMEMBER_COOKIE_SECURE,
    )
    # add login manager
    login_manager.init_app(app)

    # Register blueprints here
    pref = "/api/v1/"
    if config.BP_PREFIX:
        pref = config.BP_PREFIX + ("/api/v1" if config.BP_PREFIX.startswith("/") else "/api/v1/")

    app.register_blueprint(main_bp, url_prefix=pref)

    CORS(app, supports_credentials=True)

    return app


if __name__ == "__main__":
    app = create_app()
    dot = dotenv_values("../.env")
    config.CW_MAX_SUB = int(dot.get("VITE_CW_MAX_SUB", 4))
    app.run(port=int(dot.get("BACKEND_PORT", 8000)))
