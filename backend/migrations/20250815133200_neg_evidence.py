"""
This module contains a Caribou migration.

Migration Name: neg_evidence
Migration Version: 20250815133200
"""

TBL_EV = "evidence"

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ev = cur.execute(f"SELECT * FROM {TBL_EV};").fetchall()

    cur.execute(f"DELETE FROM {TBL_EV}")
    cur.execute(f"DROP TABLE {TBL_EV}")

    cur.execute(
        f"""CREATE TABLE {TBL_EV} (
            id  INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL,
            code_id INTEGER NOT NULL,
            tag_id  INTEGER DEFAULT NULL,
            type    INTEGER NOT NULL,
            description TEXT NOT NULL,
            filepath    TEXT,
            created INTEGER NOT NULL,
            created_by  INTEGER NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
            FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
        );"""
    )

    for e in ev:
        e["type"] = 1

    # add evidence again
    cur.executemany(
        """INSERT INTO evidence (
            id,
            item_id, tag_id, code_id,
            created, created_by,
            type,
            description,
            filepath
        ) VALUES (
            :id,
            :item_id, :tag_id, :code_id,
            :created, :created_by,
            :type,
            :description,
            :filepath
        );""",
        ev
    )
    print(f"refreshed {cur.rowcount} evidence pieces")

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ev = cur.execute(f"SELECT * FROM {TBL_EV};").fetchall()

    cur.execute(f"DELETE FROM {TBL_EV}")
    cur.execute(f"DROP TABLE {TBL_EV}")

    cur.execute(
        f"""CREATE TABLE {TBL_EV} (
            id  INTEGER PRIMARY KEY,
            item_id INTEGER NOT NULL,
            code_id INTEGER NOT NULL,
            tag_id  INTEGER DEFAULT NULL,
            description TEXT NOT NULL,
            filepath    TEXT,
            created INTEGER NOT NULL,
            created_by  INTEGER NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
            FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE
        );"""
    )

    # add evidence again
    cur.executemany(
        """INSERT INTO evidence (
            id,
            item_id, tag_id, code_id,
            created, created_by,
            description,
            filepath
        ) VALUES (
            :id,
            :item_id, :tag_id, :code_id,
            :created, :created_by,
            :description,
            :filepath
        );""",
        ev
    )

    print(f"refreshed {cur.rowcount} evidence pieces")

    connection.commit()
