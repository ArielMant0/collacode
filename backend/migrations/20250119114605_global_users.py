"""
This module contains a Caribou migration.

Migration Name: global_users
Migration Version: 20250119114605
"""


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all users
    users = cur.execute("SELECT * FROM users;").fetchall()
    updates = cur.execute("SELECT * FROM update_times;").fetchall()

    # delete users table
    cur.execute("DELETE FROM users;")
    cur.execute("DELETE FROM update_times;")
    cur.execute("DROP TABLE users;")
    cur.execute("DROP TABLE update_times;")

    # create new users table
    cur.execute(
        """CREATE TABLE users (
        id	INTEGER PRIMARY KEY,
        login_id  TEXT,
        name	TEXT NOT NULL UNIQUE,
        pw_hash	TEXT NOT NULL,
        role	TEXT NOT NULL,
        email	TEXT);"""
    )

    cur.executemany(
        "INSERT OR IGNORE INTO users (id, login_id, name, pw_hash, role, email) VALUES (:id, :login_id, :name, :pw_hash, :role, :email);",
        users,
    )

    # create new project users table
    cur.execute(
        """CREATE TABLE project_users (
        id	INTEGER PRIMARY KEY,
        user_id  INTEGER NOT NULL,
        dataset_id	INTEGER NOT NULL,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
        UNIQUE (user_id, dataset_id));"""
    )

    cur.executemany(
        "INSERT INTO project_users (user_id, dataset_id) VALUES (?, ?);",
        [(u["id"], u["dataset_id"]) for u in users],
    )

    # create new updates table
    cur.execute(
        """CREATE TABLE update_times (
        id	INTEGER PRIMARY KEY,
        name	TEXT NOT NULL,
        dataset_id	INTEGER NOT NULL,
        timestamp INTEGER NOT NULL,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
        CONSTRAINT uc_combi UNIQUE (name, dataset_id));"""
    )

    ds = cur.execute("SELECT id FROM datasets;").fetchone()
    for u in updates:
        u["dataset_id"] = ds["id"]

    cur.executemany(
        "INSERT INTO update_times (id, name, dataset_id, timestamp) VALUES (:id, :name, :dataset_id, :timestamp);",
        updates,
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all users
    users = cur.execute(
        "SELECT * FROM project_users du INNER JOIN users u ON du.user_id = u.id;"
    ).fetchall()
    updates = cur.execute("SELECT * FROM update_times;").fetchall()

    # delete users table
    cur.execute("DELETE FROM project_users;")
    cur.execute("DELETE FROM update_times;")
    cur.execute("DELETE FROM users;")
    cur.execute("DROP TABLE users;")
    cur.execute("DROP TABLE update_times;")
    cur.execute("DROP TABLE project_users;")

    # create users table
    cur.execute(
        """CREATE TABLE users (
        id	INTEGER PRIMARY KEY,
        dataset_id	INTEGER NOT NULL,
        login_id  TEXT,
        name	TEXT NOT NULL UNIQUE,
        pw_hash	TEXT NOT NULL,
        role	TEXT NOT NULL,
        email	TEXT,
        FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE);"""
    )

    cur.executemany(
        "INSERT OR IGNORE INTO users (id, dataset_id, login_id, name, pw_hash, role, email) VALUES (:id, :dataset_id, :login_id, :name, :pw_hash, :role, :email);",
        users,
    )

    # create updates table
    cur.execute(
        """CREATE TABLE update_times (
        id	INTEGER PRIMARY KEY,
        name	TEXT NOT NULL UNIQUE,
        timestamp INTEGER NOT NULL);"""
    )

    cur.executemany(
        "INSERT OR IGNORE INTO update_times (id, name, timestamp) VALUES (:id, :name, :timestamp);",
        updates,
    )

    connection.commit()
