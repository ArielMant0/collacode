"""
This module contains a Caribou migration.

Migration Name: auth
Migration Version: 20241123221414
"""

from argon2 import PasswordHasher


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    users = cur.execute("SELECT * FROM users;").fetchall()

    cur.execute("DELETE FROM users;")
    cur.execute("DROP TABLE users;")

    cur.execute(
        """CREATE TABLE "users" (
        "id"	integer,
        "login_id"  text,
        "dataset_id"	integer NOT NULL,
        "name"	text NOT NULL UNIQUE,
        "pw_hash"	text NOT NULL,
        "role"	text NOT NULL,
        "email"	text,
        PRIMARY KEY("id"),
        CONSTRAINT "fk_dataset" FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE);"""
    )

    ph = PasswordHasher()

    for u in users:
        u["pw_hash"] = ph.hash(u["name"])
        cur.execute(
            "INSERT INTO users (id, dataset_id, name, pw_hash, role, email) VALUES (:id, :dataset_id, :name, :pw_hash, :role, :email);",
            u,
        )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    users = cur.execute("SELECT * FROM users;").fetchall()

    cur.execute("DELETE FROM users;")
    cur.execute("DROP TABLE users;")

    cur.execute(
        """CREATE TABLE "users" (
        "id"	integer,
        "dataset_id"	integer NOT NULL,
        "name"	text NOT NULL UNIQUE,
        "role"	text NOT NULL,
        "email"	text,
        PRIMARY KEY("id"),
        CONSTRAINT "fk_dataset" FOREIGN KEY("dataset_id") REFERENCES "datasets"("id") ON DELETE CASCADE);"""
    )

    for u in users:
        cur.execute(
            "INSERT INTO users (id, dataset_id, name, role, email) VALUES (:id, :dataset_id, :name, :role, :email);",
            u,
        )

    connection.commit()
