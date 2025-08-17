import config
import os
import re
import argparse
import sqlite3
import app.db_wrapper as dbw

from pathlib import Path

def is_valid_username(name):
    # new RegExp(/^[\w\-\. ]+$/, "gi")
    return len(re.findall("^[\w\-\. ]+$", name, re.IGNORECASE)) > 0

def is_valid_password(pw):
    # new RegExp(/^[\w\-\.\$#&\*\+\,\; ]+$/, "gi")
    return len(re.findall("^[\w\-\.\$#&\*\+\,\; ]+$", pw, re.IGNORECASE)) > 0

def add_user(name, pw, role=None, email=None):
    if not is_valid_username(name):
        print("invalid username")
        return

    if not is_valid_password(pw):
        print("invalid password")
        return

    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()

    try:
        if dbw.has_user_by_name(cur, name):
            print(f"username '{name}' already exists")
            return

        dbw.add_user_return_id(cur, {
            "name": name,
            "password": pw,
            "role": role,
            "email": email
        })
        con.commit()

        print(f"added user {name} to database")
    except ValueError as e:
        print(e)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='AddUser', description='Add a new database user')
    parser.add_argument('name')
    parser.add_argument('password')
    parser.add_argument('-r', '--role', choices=["guest", "collaborator", "admin"])
    parser.add_argument('-e', '--email')
    args = parser.parse_args()
    add_user(args.name, args.password, args.role, args.email)
