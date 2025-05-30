"""
This module contains a Caribou migration.

Migration Name: obj_resolved_by
Migration Version: 20250530132530
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    objs = cur.execute("SELECT * FROM objections;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM objections;")
    cur.execute("DROP TABLE objections;")

    for d in objs:

        # open
        if d["status"] == 1:
            d["resolved_by"] = None
            d["resolved"] = None
        # closed
        else:
            d["resolved_by"] = d["user_id"]
            d["resolved"] = d["created"]

    # create new users table
    cur.execute(
        """CREATE TABLE objections (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            code_id INTEGER NOT NULL,
            item_id INTEGER DEFAULT NULL,
            tag_id INTEGER DEFAULT NULL,
            action INTEGER NOT NULL,
            status INTEGER DEFAULT 1,
            explanation TEXT NOT NULL,
            resolution TEXT DEFAULT NULL,
            resolved_by INTEGER DEFAULT NULL,
            created INTEGER NOT NULL,
            resolved INTEGER DEFAULT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
            FOREIGN KEY (resolved_by) REFERENCES users (id) ON DELETE SET NULL
        );"""
    )

    cur.executemany(
        "INSERT INTO objections (id, user_id, code_id, item_id, tag_id, action, status, explanation, resolution, resolved_by, created, resolved) " +
        "VALUES (:id, :user_id, :code_id, :item_id, :tag_id, :action, :status, :explanation, :resolution, :resolved_by, :created, :resolved);",
        objs,
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    objs = cur.execute("SELECT * FROM objections;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM objections;")
    cur.execute("DROP TABLE objections;")

    # create new users table
    cur.execute(
        """CREATE TABLE objections (
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
        );"""
    )

    cur.executemany(
        "INSERT INTO objections (id, user_id, code_id, item_id, tag_id, action, status, explanation, resolution, created) " +
        "VALUES (:id, :user_id, :code_id, :item_id, :tag_id, :action, :status, :explanation, :resolution, :created);",
        objs,
    )

    connection.commit()

