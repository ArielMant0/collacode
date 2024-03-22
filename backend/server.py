from flask import Flask
from flask_cors import CORS

from app import bp as main_bp

def create_app():
    app = Flask(__name__)
    app.config["DEBUG"] = False
    # Register blueprints here
    app.register_blueprint(main_bp)#, url_prefix="/colladata")
    CORS(app)
    return app

app = create_app()
app.run(port=8000)