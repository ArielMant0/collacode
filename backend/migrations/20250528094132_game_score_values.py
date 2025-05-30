"""
This module contains a Caribou migration.

Migration Name: game_score_values
Migration Version: 20250528094132
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    scores = cur.execute("SELECT * FROM game_scores;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM game_scores;")
    cur.execute("DROP TABLE game_scores;")

    for d in scores:
        mulWin = 1
        mulLoss = 0
        # matching game or trivia game
        if d["game_id"] == 1 or d["game_id"] == 4:
            mulWin = 3 + d["difficulty"]
            mulLoss = 1
        # where am i game
        elif d["game_id"] == 2:
            mulWin = 5
            mulLoss = 50
        # who am i game
        elif d["game_id"] == 3:
            mulWin = 10
            mulLoss = 10
        # set game
        elif d["game_id"] == 5:
            mulWin = 2

        d["avg_score"] = (d["wins"] * mulWin + (d["played"]-d["wins"]) * mulLoss) / d["played"]


    # create new users table
    cur.execute(
        """CREATE TABLE game_scores (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            code_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            played INTEGER NOT NULL,
            wins INTEGER NOT NULL,
            avg_score REAL DEFAULT 0,
            streak_current INTEGER DEFAULT 0,
            streak_highest INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
            UNIQUE (game_id, difficulty, user_id, code_id)
        );"""
    )

    cur.executemany(
        "INSERT INTO game_scores (id, user_id, code_id, game_id, difficulty, played, wins, avg_score, streak_current, streak_highest) " +
        "VALUES (:id, :user_id, :code_id, :game_id, :difficulty, :played, :wins, :avg_score, :streak_current, :streak_highest);",
        scores,
    )

    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    scores = cur.execute("SELECT * FROM game_scores;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM game_scores;")
    cur.execute("DROP TABLE game_scores;")

    # create new users table
    cur.execute(
        """CREATE TABLE game_scores (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            code_id INTEGER NOT NULL,
            game_id INTEGER NOT NULL,
            difficulty INTEGER NOT NULL,
            played INTEGER NOT NULL,
            wins INTEGER NOT NULL,
            streak_current INTEGER DEFAULT 0,
            streak_highest INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
            UNIQUE (game_id, difficulty, user_id, code_id)
        );"""
    )

    cur.executemany(
        "INSERT INTO game_scores (id, user_id, code_id, game_id, difficulty, played, wins, streak_current, streak_highest) " +
        "VALUES (:id, :user_id,: code_id, :game_id, :difficulty, :played, :wins, :streak_current, :streak_highest);",
        scores,
    )

    connection.commit()
