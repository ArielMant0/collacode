"""
This module contains a Caribou migration.

Migration Name: externalization_groups
Migration Version: 20241101172035
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
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    data = cur.execute("SELECT * FROM externalizations;").fetchall()

    for e in data:
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]
        ev = []
        for t in e["tags"]:
            ev = ev + cur.execute("SELECT * FROM evidence WHERE game_id = ? AND tag_id = ? AND code_id = ?;", (e["game_id"], t["tag_id"], e["code_id"])).fetchall()
        e["evidence"] = [d["id"] for d in ev]

    cur.execute("DELETE FROM externalizations;")
    cur.execute("DROP TABLE externalizations;")
    connection.commit()

    cur.execute("""CREATE TABLE "ext_groups" (
        "id"	integer,
        "game_id"	INTEGER NOT NULL,
        "code_id"	INTEGER NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
        FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE
    );""")
    cur.execute("""CREATE TABLE "externalizations" (
        "id"	INTEGER NOT NULL UNIQUE,
        "group_id"	INTEGER NOT NULL,
        "name"	TEXT NOT NULL,
        "description"	TEXT NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("group_id") REFERENCES "ext_groups"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE
    );""")
    cur.execute("""CREATE TABLE "ext_ev_connections" (
        "id"	INTEGER NOT NULL UNIQUE,
        "ext_id"    INTEGER NOT NULL,
        "ev_id" INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("ext_id") REFERENCES "externalizations"("id") ON DELETE CASCADE,
        FOREIGN KEY("ev_id") REFERENCES "evidence"("id") ON DELETE CASCADE
    );""")

    for e in data:
        # add externalization group
        group = cur.execute("INSERT INTO ext_groups (game_id, code_id, created, created_by) VALUES (:game_id, :code_id, :created, :created_by) RETURNING id;", e).fetchone()

        e["group_id"] = group["id"]
        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, group_id, name, description, created, created_by) VALUES (:id, :group_id, :name, :description, :created, :created_by);",
            e
        ).fetchone()

        # add category connections
        for d in e["categories"]:
            cur.execute("INSERT OR REPLACE INTO ext_cat_connections (id, cat_id, ext_id) VALUES (:id, :cat_id, :ext_id);", d)

        # add tag connections
        for d in e["tags"]:
            cur.execute("INSERT OR REPLACE INTO ext_tag_connections (id, tag_id, ext_id) VALUES (:id, :tag_id, :ext_id);", d)

        # add evidence connections
        for d in e["evidence"]:
            cur.execute("INSERT OR REPLACE INTO ext_ev_connections (ev_id, ext_id) VALUES (?, ?);", (d, e["id"]))

        # add evidence agreements
        for d in e["agreements"]:
            cur.execute("INSERT OR REPLACE INTO ext_agreements (id, ext_id, created_by, value) VALUES (:id, :ext_id, :created_by, :value);", d)

def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    groups = cur.execute("SELECT * FROM ext_groups;").fetchall()
    ext_cat_conns = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_tag_conns = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    data = cur.execute("SELECT * FROM externalizations;").fetchall()

    for e in data:
        g = [d for d in groups if d["id"] == e["group_id"]][0]
        e["game_id"] = g["game_id"]
        e["code_id"] = g["code_id"]
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]

    cur.execute("DELETE FROM externalizations;")
    cur.execute("DROP TABLE externalizations;")

    cur.execute("DELETE FROM ext_ev_connections;")
    cur.execute("DROP TABLE ext_ev_connections;")

    cur.execute("DELETE FROM ext_groups;")
    cur.execute("DROP TABLE ext_groups;")
    connection.commit()

    cur.execute("""CREATE TABLE "externalizations" (
        "id"	INTEGER NOT NULL UNIQUE,
        "game_id"	INTEGER NOT NULL,
        "code_id"	INTEGER NOT NULL,
        "name"	TEXT NOT NULL,
        "description"	TEXT NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE,
        FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE
    );""")

    for e in data:
        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, game_id, code_id, name, description, created, created_by) VALUES (:id, :game_id, :code_id, :name, :description, :created, :created_by);",
            e
        ).fetchone()

        # add category connections
        for d in e["categories"]:
            cur.execute("INSERT OR IGNORE INTO ext_cat_connections (id, cat_id, ext_id) VALUES (:id, :cat_id, :ext_id);", d)

        # add tag connections
        for d in e["tags"]:
            cur.execute("INSERT OR IGNORE INTO ext_tag_connections (id, tag_id, ext_id) VALUES (:id, :tag_id, :ext_id);", d)

        # add evidence agreements
        for d in e["agreements"]:
            cur.execute("INSERT OR IGNORE INTO ext_agreements (id, ext_id, created_by, value) VALUES (:id, :ext_id, :created_by, :value);", d)

