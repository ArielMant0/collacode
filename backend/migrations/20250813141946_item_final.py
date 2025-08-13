"""
This module contains a Caribou migration.

Migration Name: item_final
Migration Version: 20250813141946
"""
from datetime import datetime, timezone

TBL_USERS = "users"
TBL_USER_SESS = "user_sessions"
TBL_ITEMS = "items"
TBL_ITEMS_FINAL = "items_finalized"

def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # create new table
    cur.execute(
        f"""CREATE TABLE {TBL_ITEMS_FINAL} (
            id  INTEGER PRIMARY KEY,
            item_id  INTEGER NOT NULL,
            user_id  INTEGER NOT NULL,
            timestamp  INTEGER NOT NULL,
            FOREIGN KEY (item_id) REFERENCES {TBL_ITEMS} (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES {TBL_USERS} (id) ON DELETE CASCADE
        )"""
    )

    users = cur.execute(f"SELECT * FROM {TBL_USERS};").fetchall()

    cur.execute(f"DELETE FROM {TBL_USERS}")
    cur.execute(f"DROP TABLE {TBL_USERS}")

    # update user table
    cur.execute(
        f"""CREATE TABLE {TBL_USERS} (
            id	INTEGER PRIMARY KEY,
            name	TEXT NOT NULL UNIQUE,
            pw_hash	TEXT NOT NULL,
            role	TEXT NOT NULL,
            email	TEXT
        );"""
    )

    cur.executemany(
        f"INSERT INTO {TBL_USERS} (id, name, pw_hash, role, email) VALUES " +
        "(:id, :name, :pw_hash, :role, :email)",
        users
    )

    # create a new user session table
    cur.execute(
        f"""CREATE TABLE {TBL_USER_SESS} (
            id  INTEGER PRIMARY KEY,
            user_id  INTEGER NOT NULL,
            session_id  TEXT NOT NULL UNIQUE,
            last_update  INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES {TBL_USERS} (id) ON DELETE CASCADE
        )"""
    )

    now = get_millis()
    cur.executemany(
        f"INSERT INTO {TBL_USER_SESS} (user_id, session_id, last_update) VALUES (?,?,?);",
        [(d["id"], d["login_id"], now) for d in users if d["login_id"] is not None]
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    cur.execute(f"DELETE FROM {TBL_ITEMS_FINAL}")
    cur.execute(f"DROP TABLE {TBL_ITEMS_FINAL}")

    cur.execute(f"DELETE FROM {TBL_USER_SESS}")
    cur.execute(f"DROP TABLE {TBL_USER_SESS}")

    users = cur.execute(f"""
        SELECT u.*, s.session_id as login_id FROM {TBL_USERS} u
        LEFT JOIN {TBL_USER_SESS} s ON u.id = s.user_id;
    """).fetchall()

    cur.execute(f"DELETE FROM {TBL_USERS}")
    cur.execute(f"DROP TABLE {TBL_USERS}")

    # update user table
    cur.execute(
        f"""CREATE TABLE {TBL_USERS} (
            id	INTEGER PRIMARY KEY,
            name	TEXT NOT NULL UNIQUE,
            login_id	TEXT DEFAULT NULL,
            pw_hash	TEXT NOT NULL,
            role	TEXT NOT NULL,
            email	TEXT
        );"""
    )

    cur.executemany(
        f"INSERT INTO {TBL_USERS} (id, name, login_id, pw_hash, role, email) VALUES " +
        "(:id, :name, :login_id, :pw_hash, :role, :email)",
        users
    )

    connection.commit()

