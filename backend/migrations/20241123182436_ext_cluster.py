"""
This module contains a Caribou migration.

Migration Name: ext_cluster
Migration Version: 20241123182436
"""

import logging

logger = logging.getLogger(__name__)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ext_cat_conns = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_tag_conns = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_ev_conns = cur.execute("SELECT * FROM ext_ev_connections;").fetchall()
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    data = cur.execute("SELECT * FROM externalizations;").fetchall()

    for e in data:
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["evidence"] = [d for d in ext_ev_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]

    cur.execute("DELETE FROM externalizations;")
    cur.execute("DROP TABLE externalizations;")
    connection.commit()

    cur.execute(
        """CREATE TABLE "externalizations" (
        "id"	INTEGER NOT NULL UNIQUE,
        "group_id"	INTEGER NOT NULL,
        "name"	TEXT NOT NULL,
        "cluster"	TEXT NOT NULL DEFAULT "_base_",
        "description"	TEXT NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("group_id") REFERENCES "ext_groups"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE);"""
    )

    for e in data:

        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, group_id, name, description, created, created_by) VALUES (:id, :group_id, :name, :description, :created, :created_by);",
            e,
        ).fetchone()

        # add category connections
        for d in e["categories"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_cat_connections (id, cat_id, ext_id) VALUES (:id, :cat_id, :ext_id);",
                d,
            )

        # add tag connections
        for d in e["tags"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_tag_connections (id, tag_id, ext_id) VALUES (:id, :tag_id, :ext_id);",
                d,
            )

        # add evidence connections
        for d in e["evidence"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_ev_connections (id, ev_id, ext_id) VALUES (:id, :ev_id, :ext_id);",
                d,
            )

        # add agreements
        for d in e["agreements"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_agreements (id, ext_id, created_by, value) VALUES (:id, :ext_id, :created_by, :value);",
                d,
            )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ext_cat_conns = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_tag_conns = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_ev_conns = cur.execute("SELECT * FROM ext_ev_connections;").fetchall()
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    data = cur.execute("SELECT * FROM externalizations;").fetchall()

    for e in data:
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["evidence"] = [d for d in ext_ev_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]

    cur.execute("DELETE FROM externalizations;")
    cur.execute("DROP TABLE externalizations;")

    connection.commit()

    cur.execute(
        """CREATE TABLE "externalizations" (
        "id"	INTEGER NOT NULL UNIQUE,
        "group_id"	INTEGER NOT NULL,
        "name"	TEXT NOT NULL,
        "description"	TEXT NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("group_id") REFERENCES "ext_groups"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE);"""
    )

    for e in data:
        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, group_id, name, description, created, created_by) VALUES (:id, :group_id, :name, :description, :created, :created_by);",
            e,
        ).fetchone()

        # add category connections
        for d in e["categories"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_cat_connections (id, cat_id, ext_id) VALUES (:id, :cat_id, :ext_id);",
                d,
            )

        # add tag connections
        for d in e["tags"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_tag_connections (id, tag_id, ext_id) VALUES (:id, :tag_id, :ext_id);",
                d,
            )

        # add evidence connections
        for d in e["evidence"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_ev_connections (id, ev_id, ext_id) VALUES (:id, :ev_id, :ext_id);",
                d,
            )

        # add agreements
        for d in e["agreements"]:
            cur.execute(
                "INSERT OR REPLACE INTO ext_agreements (id, ext_id, created_by, value) VALUES (:id, :ext_id, :created_by, :value);",
                d,
            )

    connection.commit()
