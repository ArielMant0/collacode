"""
This module contains a Caribou migration.

Migration Name: feedback
Migration Version: 20250804111051
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # add feedback table
    cur.execute("""
        CREATE TABLE feedback (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            text    TEXT NOT NULL,
            timestamp    INTEGER NOT NULL,
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # empty and remove feedback table
    cur.execute("DELETE FROM feedback")
    cur.execute("DROP TABLE feedback")

    connection.commit()
