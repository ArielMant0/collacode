import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", "data.db")

db = sqlite3.connect(DB_PATH, check_same_thread=False)