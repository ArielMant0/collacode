from flask import Flask
from flask_cors import CORS

from app import bp as main_bp

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = True
    app.config['MAX_CONTENT_LENGTH'] = 3 * 1000 * 1000
    # Register blueprints here
    app.register_blueprint(main_bp)#, url_prefix="/colladata")
    CORS(app)
    return app

app = create_app()
app.run(port=8000)