"""
This module contains a Caribou migration.

Migration Name: rating_per_game
Migration Version: 20250812143338
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ratings = cur.execute("SELECT * FROM ratings;").fetchall()
    feedback = cur.execute("SELECT * FROM feedback;").fetchall()

    # delete ratings table
    cur.execute("DELETE FROM ratings")
    cur.execute("DELETE FROM feedback")
    cur.execute("DROP TABLE ratings")
    cur.execute("DROP TABLE feedback")

    game_by_client = {}

    for r in ratings:
        sub = cur.execute(
            "SELECT game_id FROM submissions WHERE client_id = ? ORDER BY timestamp ASC",
            (r["client_id"],)
        ).fetchone()

        if sub:
            game_by_client[r["client_id"]] = sub["game_id"]
            r["game_id"] = sub["game_id"]
        else:
            r["game_id"] = 1

    # add ratings table
    cur.execute("""
        CREATE TABLE ratings (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            game_id    INTEGER NOT NULL,
            rating_ease    INTEGER DEFAULT NULL,
            rating_fun    INTEGER DEFAULT NULL,
            rating_satisfaction    INTEGER DEFAULT NULL,
            rating_preference    INTEGER DEFAULT NULL,
            timestamp    INTEGER NOT NULL,
            UNIQUE(client_id,game_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    cur.executemany(
        "INSERT INTO ratings (client_id, game_id, rating_ease, rating_fun, rating_satisfaction, " +
        "rating_preference, timestamp) VALUES (:client_id, :game_id, :rating_ease, :rating_fun, " +
        ":rating_satisfaction, :rating_preference, :timestamp);",
        ratings
    )

    for f in feedback:
        if f["client_id"] in game_by_client:
            f["game_id"] = sub["game_id"]
        else:
            f["game_id"] = 1

    # add feedback table
    cur.execute("""
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            game_id    INTEGER NOT NULL,
            text    TEXT NOT NULL,
            timestamp    INTEGER NOT NULL,
            UNIQUE(client_id,game_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    cur.executemany(
        "INSERT INTO feedback (client_id, game_id, text, timestamp) VALUES (:client_id, " +
        ":game_id, :text, :timestamp);",
        feedback
    )

    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ratings = cur.execute("SELECT * FROM ratings;").fetchall()
    feedback = cur.execute("SELECT * FROM feedback;").fetchall()

    # delete ratings table
    cur.execute("DELETE FROM ratings")
    cur.execute("DELETE FROM feedback")
    cur.execute("DROP TABLE ratings")
    cur.execute("DROP TABLE feedback")

    # add ratings table
    cur.execute("""
        CREATE TABLE ratings (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            rating_ease    INTEGER DEFAULT NULL,
            rating_fun    INTEGER DEFAULT NULL,
            rating_satisfaction    INTEGER DEFAULT NULL,
            rating_preference    INTEGER DEFAULT NULL,
            timestamp    INTEGER NOT NULL,
            UNIQUE(client_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    cur.executemany(
        "INSERT INTO ratings (client_id, rating_ease, rating_fun, rating_satisfaction, " +
        "rating_preference, timestamp) VALUES (:client_id, :rating_ease, :rating_fun, " +
        ":rating_satisfaction, :rating_preference, :timestamp);",
        ratings
    )


    # add feedback table
    cur.execute("""
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            text    TEXT NOT NULL,
            timestamp    INTEGER NOT NULL,
            UNIQUE(client_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    cur.executemany(
        "INSERT INTO feedback (client_id, text, timestamp) VALUES (:client_id, " +
        ":text, :timestamp);",
        feedback
    )

    connection.commit()
