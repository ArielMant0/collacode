"""
This module contains a Caribou migration.

Migration Name: game_tracking
Migration Version: 20250309162729
"""
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    cur = connection.cursor()

    # add score table
    cur.execute("""CREATE TABLE game_scores (
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
    );""")

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    cur = connection.cursor()
    # delete score table
    cur.execute("DELETE FROM game_scores;")
    cur.execute("DROP TABLE game_scores;")

    connection.commit()
