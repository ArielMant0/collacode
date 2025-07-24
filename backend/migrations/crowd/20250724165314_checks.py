"""
This module contains a Caribou migration.

Migration Name: checks
Migration Version: 20250724165314
"""

from datetime import datetime, timezone

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing submissions
    subs = cur.execute("SELECT * FROM submissions").fetchall()
    clients = cur.execute("SELECT * FROM client_info").fetchall()

    new_clients = []
    for d in subs:
        cl = next((c for c in clients if c["guid"] == d["guid"]), None)
        if cl is None:
            new_clients.append(c["guid"])
        else:
            d["client_id"] = cl["id"]

    # delete submissions table
    cur.execute("DELETE FROM submissions")
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE submissions")
    cur.execute("DROP TABLE client_info")

    # modify clients table
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

    # insert old clients
    cur.executemany(
        "INSERT INTO client_info (guid, ip, cwId, cwSource, method, requests_recent, recent_update, last_update) " +
        "VALUES (:guid, :ip, :cwId, :cwSource, :method, :requests_recent, :recent_update, :last_update);",
        clients,
    )

    if len(new_clients) > 0:
        now = int(datetime.now(timezone.utc).timestamp() * 1000)
        # insert new clients
        cur.executemany(
            "INSERT INTO client_info (guid, recent_update, last_update) VALUES (?, ?, ?);",
            [(guid, now, now) for guid in new_clients],
        )

    # modify submissions table
    cur.execute("""
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            game_id	INTEGER NOT NULL,
            client_id	INTEGER NOT NULL,
            timestamp	INTEGER NOT NULL,
            data	BLOB DEFAULT NULL,
            UNIQUE(target_id,game_id,client_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    # insert submissions
    cur.executemany(
        "INSERT INTO submissions (id, dataset_id, target_id, game_id, client_id, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :game_id, :client_id, :timestamp, :data);",
        subs
    )

    # commit changes
    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing submissions
    subs = cur.execute("SELECT * FROM submissions").fetchall()
    clients = cur.execute("SELECT * FROM client_info").fetchall()

    for d in subs:
        cl = next((c for c in clients if c["id"] == d["client_id"]), None)
        d["guid"] = cl["guid"]

    # delete submissions table
    cur.execute("DELETE FROM submissions")
    cur.execute("DELETE FROM client_info")
    cur.execute("DROP TABLE submissions")
    cur.execute("DROP TABLE client_info")

    # modify clients table
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

    # insert old clients
    cur.executemany(
        "INSERT INTO client_info (guid, ip, cwId, cwSource, method, requests_recent, recent_update, last_update) " +
        "VALUES (:guid, :ip, :cwId, :cwSource, :method, :requests_recent, :recent_update, :last_update);",
        clients,
    )

    # modify submissions table
    cur.execute("""
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            game_id	INTEGER NOT NULL,
            guid	TEXT NOT NULL,
            timestamp	INTEGER NOT NULL,
            data	BLOB DEFAULT NULL,
            UNIQUE(target_id,game_id,guid)
        )"""
    )

    # insert submissions
    cur.executemany(
        "INSERT INTO submissions (id, dataset_id, target_id, game_id, guid, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :game_id, :guid, :timestamp, :data);",
        subs
    )

    # commit changes
    connection.commit()
