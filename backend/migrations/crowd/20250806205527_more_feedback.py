"""
This module contains a Caribou migration.

Migration Name: more_feedback
Migration Version: 20250806205527
"""

def upgrade(connection):
    # add your upgrade step here
    cur = connection.cursor()

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

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    cur = connection.cursor()

    # empty and remove ratings table
    cur.execute("DELETE FROM ratings")
    cur.execute("DROP TABLE ratings")

    connection.commit()
