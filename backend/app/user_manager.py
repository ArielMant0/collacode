from uuid import uuid4

from app.extensions import db
from argon2 import PasswordHasher
from db_wrapper import get_millis, dict_factory

from table_constants import TBL_USERS, TBL_USER_SESS

class User:

    def __init__(self, id, session_id, name, password_hash, role="collaborator"):
        self.id = id
        self.session_id = session_id
        self.name = name
        self.password_hash = password_hash
        self.role = role
        self.can_edit = role != "guest"
        self.is_admin = role == "admin"
        self.is_active = False
        self.is_anonymous = True
        self.is_authenticated = False

    def authenticate(self, password):
        try:
            ph = PasswordHasher()
            ph.verify(self.password_hash, password)
            self.is_anonymous = False
            self.is_active = True
            self.is_authenticated = True
        except:
            self.is_anonymous = True
            self.is_active = False
            self.is_authenticated = False

    def get_id(self):
        return str(self.session_id)

    def try_change_pwd(self, old_pw, new_pw):
        if not self.is_authenticated:
            return False

        ph = PasswordHasher()
        old_match = ph.verify(self.password_hash, old_pw)

        if old_match:

            new_hash = ph.hash(new_pw)
            # make sure passwords are different
            if new_hash == self.password_hash:
                return False

            # set new password hash
            self.password_hash = new_hash
            cur = db.cursor()
            # update has in database
            cur.execute(f"UPDATE {TBL_USERS} SET pw_hash = ? WHERE id = ?;", (new_hash, self.id))
            db.commit()
            return True

        return False

    def __str__(self):
        return f"{self.name}, authenticated: {'yes' if self.is_authenticated else 'no'} - ({self.session_id})"


def get_user(session_id):
    cur = db.cursor()
    cur.row_factory = dict_factory
    sess = cur.execute(f"SELECT * FROM {TBL_USER_SESS} WHERE session_id = ?;", (session_id,)).fetchone()
    if sess is None:
        return None

    user = cur.execute(f"SELECT * FROM {TBL_USERS} WHERE id = ?;", (sess["user_id"],)).fetchone()
    if user is None:
        return None

    user_obj = User(user["id"], sess["session_id"], user["name"], user["pw_hash"], user["role"])
    user_obj.is_anonymous = False
    user_obj.is_active = True
    user_obj.is_authenticated = True
    try:
        cur.execute(
            f"UPDATE {TBL_USER_SESS} SET last_update = ? WHERE id = ?;",
            (get_millis(), sess["id"])
        )
        db.commit()
    except:
        print("user session update failed")

    return user_obj


def get_user_by_name(name):
    cur = db.cursor()
    cur.row_factory = dict_factory
    user = cur.execute(f"SELECT * FROM {TBL_USERS} WHERE name = ? COLLATE NOCASE;", (name,)).fetchone()
    if user is None:
        return None

    lid = uuid4()
    while (
        cur.execute(f"SELECT * FROM {TBL_USER_SESS} WHERE session_id = ?;", (str(lid),)).fetchone() is not None
    ):
        lid = uuid4()

    user["session_id"] = lid

    try:
        cur.execute(
            f"INSERT INTO {TBL_USER_SESS} (user_id, session_id, last_update) VALUES (?, ?, ?);",
            (user["id"],str(lid), get_millis())
        )
        db.commit()
    except:
        print("user session insert failed")

    return User(user["id"], user["session_id"], user["name"], user["pw_hash"], user["role"])
