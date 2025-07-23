"""
This module contains a Caribou migration.

Migration Name: game_variant
Migration Version: 20250723114219
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing clients
    clients = cur.execute("SELECT * FROM client_info").fetchall()
    for d in clients:
        d["cwId"] = None
        d["cwSource"] = None
        d["method"] = 0

    # delete similarity table
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE client_info")

    # modify item similarity table
    cur.execute("""
        CREATE TABLE client_info (
            id INTEGER PRIMARY KEY,
            guid    TEXT NOT NULL,
            ip	TEXT DEFAULT NULL,
            cwId   TEXT DEFAULT NULL,
            cwSource   TEXT DEFAULT NULL,
            method   INTEGER DEFAULT 0,
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

    # commit changes
    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing clients
    clients = cur.execute("SELECT * FROM client_info").fetchall()
    for d in clients:
        # get all submissions for this client
        subs = cur.execute("SELECT * FROM submissions WHERE guid = ?;", (d["guid"],)).fetchall()
        d["request_count"] = d["requests_recent"] + len(subs)

    # delete clients table
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE client_info")

    # modify clients table
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
        clients,
    )

    # commit changes
    connection.commit()
