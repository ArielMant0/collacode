"""
This module contains a Caribou migration.

Migration Name: int_logs
Migration Version: 20250811094453
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing clients
    cur.execute("""
        CREATE TABLE interaction_logs (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            timestamp   INTEGER NOT NULL,
            action  TEXT NOT NULL,
            data    TEXT DEFAULT NULL,
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # delete clients table
    cur.execute("DELETE FROM interaction_logs")
    cur.execute("DROP TABLE interaction_logs")
