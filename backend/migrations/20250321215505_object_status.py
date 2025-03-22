"""
This module contains a Caribou migration.

Migration Name: object_status
Migration Version: 20250321215505
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    objs = cur.execute("SELECT * FROM objections;").fetchall()

    # delete objection table
    cur.execute("DELETE FROM objections;")
    cur.execute("DROP TABLE objections;")

    # create objection table
    cur.execute("""CREATE TABLE objections (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        item_id INTEGER DEFAULT NULL,
        tag_id INTEGER DEFAULT NULL,
        action INTEGER NOT NULL,
        status INTEGER DEFAULT 1,
        explanation TEXT NOT NULL,
        resolution TEXT DEFAULT NULL,
        created INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );""")

    for d in objs:
        d["status"] = 1
        d["resolution"] = None

    cur.executemany(
        "INSERT INTO objections(id, user_id, code_id, item_id, tag_id, action, status, explanation, resolution, created) " +
        "VALUES (:id, :user_id, :code_id, :item_id, :tag_id, :action, :status, :explanation, :resolution, :created);",
        objs
    )

    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    objs = cur.execute("SELECT * FROM objections;").fetchall()

    # delete objection table
    cur.execute("DELETE FROM objections;")
    cur.execute("DROP TABLE objections;")

    # create objection table
    cur.execute("""CREATE TABLE objections (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        item_id INTEGER DEFAULT NULL,
        tag_id INTEGER DEFAULT NULL,
        action INTEGER NOT NULL,
        explanation TEXT NOT NULL,
        created INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
    );""")

    for d in objs:
        d["status"] = 1

    cur.executemany(
        "INSERT INTO objections(id, user_id, code_id, item_id, tag_id, action, explanation, created) " +
        "VALUES (:id, :user_id, :code_id, :item_id, :tag_id, :action, :explanation, :created);",
        objs
    )

    connection.commit()
