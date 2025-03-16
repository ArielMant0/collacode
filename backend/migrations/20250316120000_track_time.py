"""
This module contains a Caribou migration.

Migration Name: track_time
Migration Version: 20250316120000
"""

from datetime import datetime, timezone


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    item_scores = cur.execute("SELECT * FROM game_scores_items").fetchall()
    tag_scores = cur.execute("SELECT * FROM game_scores_tags").fetchall()

    for d in item_scores:
        d["created"] = now
        d["win"] = 1 if d["right"] > 0 else 0

    for d in tag_scores:
        d["created"] = now
        d["win"] = 1 if d["right"] > 0 else 0


    # delete score tables
    cur.execute("DELETE FROM game_scores_items;")
    cur.execute("DELETE FROM game_scores_tags;")
    cur.execute("DROP TABLE game_scores_items;")
    cur.execute("DROP TABLE game_scores_tags;")

    # add score table for items
    cur.execute("""CREATE TABLE game_scores_items (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        difficulty INTEGER NOT NULL,
        win INTEGER NOT NULL,
        created INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
    );""")

    cur.executemany(
        "INSERT INTO game_scores_items(id, game_id, difficulty, code_id, user_id, item_id, created, win) " +
        "VALUES (:id, :game_id, :difficulty, :code_id, :user_id, :item_id, :created, :win);",
        item_scores
    )

    # add score table for tags (+ items)
    cur.execute("""CREATE TABLE game_scores_tags (
        id INTEGER PRIMARY KEY,
        user_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        item_id INTEGER NOT NULL,
        game_id INTEGER NOT NULL,
        difficulty INTEGER NOT NULL,
        win INTEGER NOT NULL,
        created INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES tags (id) ON DELETE CASCADE,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE
    );""")

    cur.executemany(
        "INSERT INTO game_scores_tags (id, game_id, difficulty, code_id, user_id, tag_id, item_id, created, win) " +
        "VALUES (:id, :game_id, :difficulty, :code_id, :user_id, :tag_id, :item_id, :created, :win);",
        tag_scores
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    item_scores = cur.execute("SELECT * FROM game_scores_items").fetchall()
    tag_scores = cur.execute("SELECT * FROM game_scores_tags").fetchall()

    for d in item_scores:
        d["right"] = 1 if d["win"] > 0 else 0
        d["wrong"] = 0 if d["win"] > 0 else 1

    for d in tag_scores:
        d["right"] = 1 if d["win"] > 0 else 0
        d["wrong"] = 0 if d["win"] > 0 else 1

    # delete score tables
    cur.execute("DELETE FROM game_scores_items;")
    cur.execute("DELETE FROM game_scores_tags;")
    cur.execute("DROP TABLE game_scores_items;")
    cur.execute("DROP TABLE game_scores_tags;")

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

    cur.executemany(
        "INSERT INTO game_scores_items(id, game_id, difficulty, code_id, user_id, item_id, right, wrong) " +
        "VALUES (:id, :game_id, :difficulty, :code_id, :user_id, :item_id, :right, :wrong);",
        item_scores
    )

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

    cur.executemany(
        "INSERT INTO game_scores_tags (id, game_id, difficulty, code_id, user_id, tag_id, item_id, right, wrong) " +
        "VALUES (:id, :game_id, :difficulty, :code_id, :user_id, :tag_id, :item_id, :right, :wrong);",
        tag_scores
    )

    connection.commit()
