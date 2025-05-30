import config
import os
import sqlite3
from pathlib import Path

from app.lobby_manager import LobbyManager
from flask_login import LoginManager

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", config.DATABASE_PATH).resolve()

db = sqlite3.connect(DB_PATH, check_same_thread=False)
# db.execute("PRAGMA foreign_keys = 1;")

login_manager = LoginManager()

lobby_manager = LobbyManager()
