"""
This module contains a Caribou migration.

Migration Name: track_data
Migration Version: 20250309183625
"""
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    cur = connection.cursor()

    # add score table for items
    cur.execute("""CREATE TABLE game_scores_items (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        difficulty INTEGER NOT NULL,
        right INTEGER NOT NULL,
        wrong INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        UNIQUE (game_id, difficulty, user_id, code_id, item_id)
    );""")

    # add score table for tags (+ items)
    cur.execute("""CREATE TABLE game_scores_tags (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        difficulty INTEGER NOT NULL,
        right INTEGER NOT NULL,
        wrong INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES tags (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        UNIQUE (game_id, difficulty, user_id, code_id, tag_id, item_id)
    );""")

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    cur = connection.cursor()

    # delete score tables
    cur.execute("DELETE FROM game_scores_items;")
    cur.execute("DELETE FROM game_scores_tags;")
    cur.execute("DROP TABLE game_scores_items;")
    cur.execute("DROP TABLE game_scores_tags;")

    connection.commit()
