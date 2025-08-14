import config
import os
import sqlite3
from pathlib import Path

from app.lobby_manager import LobbyManager
from flask_login import LoginManager

class AnonymousUser:

    def __init__(self):
        self.id = id
        self.session_id = None
        self.name = None
        self.password_hash = None
        self.role = None
        self.can_edit = False
        self.is_admin = False
        self.is_active = False
        self.is_anonymous = True
        self.is_authenticated = False

    def get_id(self):
        return None

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", config.DATABASE_PATH).resolve()
CROWD_DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", config.CROWD_DATABASE_PATH).resolve()

db = sqlite3.connect(DB_PATH, check_same_thread=False)
# db.execute("PRAGMA foreign_keys = 1;")
cdb = sqlite3.connect(CROWD_DB_PATH, check_same_thread=False)

login_manager = LoginManager()
login_manager.anonymous_user = AnonymousUser

lobby_manager = LobbyManager()


