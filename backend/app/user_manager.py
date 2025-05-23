from uuid import uuid4

from app.extensions import db
from argon2 import PasswordHasher
from db_wrapper import dict_factory


class User:

    def __init__(self, id, login_id, name, password_hash, role="collaborator"):
        self.id = id
        self.login_id = login_id
        self.name = name
        self.password_hash = password_hash
        self.role = role
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
        return str(self.login_id)

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
            cur.execute("UPDATE users SET pw_hash = ? WHERE id = ?;", (new_hash, self.id))
            db.commit()
            return True

        return False

    def __str__(self):
        return f"{self.name}, authenticated: {'yes' if self.is_authenticated else 'no'} - ({self.login_id})"


def get_user(user_id):
    cur = db.cursor()
    cur.row_factory = dict_factory
    user = cur.execute("SELECT * FROM users WHERE login_id = ?;", (user_id,)).fetchone()
    if user is None:
        return None

    user_obj = User(user["id"], user["login_id"], user["name"], user["pw_hash"], user["role"])
    user_obj.is_anonymous = False
    user_obj.is_active = True
    user_obj.is_authenticated = True
    return user_obj


def get_user_by_name(name):
    cur = db.cursor()
    cur.row_factory = dict_factory
    user = cur.execute("SELECT * FROM users WHERE name = ?;", (name,)).fetchone()
    if user is None:
        return None

    lid = uuid4()
    while (
        cur.execute("SELECT * FROM users WHERE login_id = ?;", (str(lid),)).fetchone() is not None
    ):
        lid = uuid4()

    user["login_id"] = lid
    cur.execute("UPDATE users SET login_id = ? WHERE id = ?;", (str(lid), user["id"]))
    db.commit()

    return User(user["id"], user["login_id"], user["name"], user["pw_hash"], user["role"])
