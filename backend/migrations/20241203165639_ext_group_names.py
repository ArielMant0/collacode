"""
This module contains a Caribou migration.

Migration Name: ext_group_names
Migration Version: 20241203165639
"""


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

    ext_groups = cur.execute("SELECT * FROM ext_groups;").fetchall()
    games = set([d["game_id"] for d in ext_groups])

    for e in data:
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["evidence"] = [d for d in ext_ev_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]

    cur.execute("DELETE FROM ext_groups;")
    cur.execute("DROP TABLE ext_groups;")
    cur.execute("DELETE FROM externalizations;")
    cur.execute("DELETE FROM ext_agreements;")
    cur.execute("DELETE FROM ext_ev_connections;")
    cur.execute("DELETE FROM ext_tag_connections;")
    cur.execute("DELETE FROM ext_cat_connections;")

    cur.execute(
        """CREATE TABLE "ext_groups" (
        "id"	INTEGER,
        "name"	TEXT NOT NULL,
        "game_id"	INTEGER NOT NULL,
        "code_id"	INTEGER NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
        FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE);"""
    )

    for game in games:
        groups = [g for g in ext_groups if g["game_id"] == game]

        for i, d in enumerate(groups):
            exts = [e for e in data if e["group_id"] == d["id"]]
            d["name"] = exts[0]["name"] if len(exts) == 1 else "group " + str(i + 1)
            cur.execute(
                "INSERT INTO ext_groups (id, name, game_id, code_id, created, created_by) "
                + "VALUES (:id, :name, :game_id, :code_id, :created, :created_by)",
                d,
            )

    for e in data:

        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, group_id, name, cluster, description, created, created_by) VALUES (:id, :group_id, :name, :cluster, :description, :created, :created_by);",
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


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ext_cat_conns = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_tag_conns = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_ev_conns = cur.execute("SELECT * FROM ext_ev_connections;").fetchall()
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    data = cur.execute("SELECT * FROM externalizations;").fetchall()

    ext_groups = cur.execute("SELECT * FROM ext_groups;").fetchall()

    for e in data:
        id = e["id"]
        e["categories"] = [d for d in ext_cat_conns if d["ext_id"] == id]
        e["tags"] = [d for d in ext_tag_conns if d["ext_id"] == id]
        e["evidence"] = [d for d in ext_ev_conns if d["ext_id"] == id]
        e["agreements"] = [d for d in ext_agree if d["ext_id"] == id]

    cur.execute("DELETE FROM ext_groups;")
    cur.execute("DROP TABLE ext_groups;")
    cur.execute("DELETE FROM externalizations;")
    cur.execute("DELETE FROM ext_agreements;")
    cur.execute("DELETE FROM ext_ev_connections;")
    cur.execute("DELETE FROM ext_tag_connections;")
    cur.execute("DELETE FROM ext_cat_connections;")

    cur.execute(
        """CREATE TABLE "ext_groups" (
        "id"	INTEGER,
        "game_id"	INTEGER NOT NULL,
        "code_id"	INTEGER NOT NULL,
        "created"	INTEGER NOT NULL,
        "created_by"	INTEGER NOT NULL,
        PRIMARY KEY("id" AUTOINCREMENT),
        FOREIGN KEY("code_id") REFERENCES "codes"("id") ON DELETE CASCADE,
        FOREIGN KEY("created_by") REFERENCES "users"("id") ON DELETE CASCADE,
        FOREIGN KEY("game_id") REFERENCES "games"("id") ON DELETE CASCADE);"""
    )

    for d in ext_groups:
        cur.execute(
            "INSERT INTO ext_groups (id, game_id, code_id, created, created_by) "
            + "VALUES (:id, :game_id, :code_id, :created, :created_by)",
            d,
        )

    for e in data:

        # add externalization
        cur.execute(
            "INSERT INTO externalizations (id, group_id, name, cluster, description, created, created_by) VALUES (:id, :group_id, :name, :cluster, :description, :created, :created_by);",
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
