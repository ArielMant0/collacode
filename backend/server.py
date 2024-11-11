from flask import Flask, Request
from flask_cors import CORS

from app import bp as main_bp
import config

class CustomRequest(Request):
    def __init__(self, *args, **kwargs):
        super(CustomRequest, self).__init__(*args, **kwargs)
        self.max_form_parts = 10

def create_app():
    app = Flask(__name__)
    app.request_class = CustomRequest
    app.config["DEBUG"] = config.DEBUG
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH
    app.config["SECRET_KEY"] = config.SECRET_KEY
    # Register blueprints here
    app.register_blueprint(main_bp)#, url_prefix="/colladata")
    CORS(app)
    return app

app = create_app()
app.run(port=8000)