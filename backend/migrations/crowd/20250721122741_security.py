"""
This module contains a Caribou migration.

Migration Name: security
Migration Version: 20250721122741
"""

from datetime import datetime, timezone

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get the number of submissions per GUID
    info = cur.execute("SELECT guid, COUNT(*) as request_count FROM submissions GROUP BY guid;").fetchall()

    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    # add other fields to the data
    for g in info:
        g["ip"] = None
        g["requests_recent"] = 0
        g["recent_update"] = now
        g["last_update"] = now

    # add new client table
    cur.execute("""
        CREATE TABLE client_info (
            id INTEGER PRIMARY KEY,
            guid    TEXT NOT NULL,
            ip	TEXT DEFAULT NULL,
            request_count   INTEGER DEFAULT 0,
            requests_recent INTEGER DEFAULT 0,
            recent_update INTEGER NOT NULL,
            last_update INTEGER NOT NULL,
            UNIQUE(guid,ip)
        )"""
    )

    # insert client data
    cur.executemany(
        "INSERT INTO client_info (guid, ip, request_count, requests_recent, recent_update, last_update) " +
        "VALUES (:guid, :ip, :request_count, :requests_recent, :recent_update, :last_update);",
        info,
    )

    # commit changes
    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # delete client info table
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE client_info")

    # commit changes
    connection.commit()

