"""
This module contains a Caribou migration.

Migration Name: cw_done
Migration Version: 20250807105051
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    clients = cur.execute("SELECT * FROM client_info").fetchall()

    # delete clients table
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE client_info")

    # get all existing clients
    cur.execute("""
        CREATE TABLE client_info (
            id INTEGER PRIMARY KEY,
            guid    TEXT NOT NULL,
            ip	TEXT DEFAULT NULL,
            cwId   TEXT DEFAULT NULL,
            cwSource   TEXT DEFAULT NULL,
            cwSubmitted INTEGER DEFAULT 0,
            method   INTEGER DEFAULT 0,
            attention_fails INTEGER DEFAULT 0,
            comprehension_fails INTEGER DEFAULT 0,
            requests_recent INTEGER DEFAULT 0,
            recent_update INTEGER NOT NULL,
            last_update INTEGER NOT NULL,
            UNIQUE(guid,ip,cwId)
        )"""
    )

    # insert clients
    cur.executemany(
        "INSERT INTO client_info (guid, ip, cwId, cwSource, method, requests_recent, recent_update, last_update) " +
        "VALUES (:guid, :ip, :cwId, :cwSource, :method, :requests_recent, :recent_update, :last_update);",
        clients,
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    clients = cur.execute("SELECT * FROM client_info").fetchall()

    # delete clients table
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE client_info")

    # get all existing clients
    cur.execute("""
        CREATE TABLE client_info (
            id INTEGER PRIMARY KEY,
            guid    TEXT NOT NULL,
            ip	TEXT DEFAULT NULL,
            cwId   TEXT DEFAULT NULL,
            cwSource   TEXT DEFAULT NULL,
            method   INTEGER DEFAULT 0,
            attention_fails INTEGER DEFAULT 0,
            comprehension_fails INTEGER DEFAULT 0,
            requests_recent INTEGER DEFAULT 0,
            recent_update INTEGER NOT NULL,
            last_update INTEGER NOT NULL,
            UNIQUE(guid,ip,cwId)
        )"""
    )

    # insert clients
    cur.executemany(
        "INSERT INTO client_info (guid, ip, cwId, cwSource, method, requests_recent, recent_update, last_update) " +
        "VALUES (:guid, :ip, :cwId, :cwSource, :method, :requests_recent, :recent_update, :last_update);",
        clients,
    )

    connection.commit()
