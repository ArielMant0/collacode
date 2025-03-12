"""
This module contains a Caribou migration.

Migration Name: objection
Migration Version: 20250312212845
"""
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    cur = connection.cursor()

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

def downgrade(connection):
    # add your downgrade step here
    cur = connection.cursor()

    # delete objection table
    cur.execute("DELETE FROM objections;")
    cur.execute("DROP TABLE objections;")
