from flask import Blueprint

bp = Blueprint("main", __name__, static_folder="../media")

from app import routes
