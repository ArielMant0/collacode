from flask import Flask
from flask_cors import CORS

from app import bp as main_bp
app = Flask(__name__)
app.config["DEBUG"] = True
# Register blueprints here
app.register_blueprint(main_bp, url_prefix="/colladata")
CORS(app)

def create_app():
    app.run(host="0.0.0.0", port=8000)