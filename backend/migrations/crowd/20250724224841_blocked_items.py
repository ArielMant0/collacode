"""
This module contains a Caribou migration.

Migration Name: blocked_items
Migration Version: 20250724224841
"""
import json

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def decode_data(data):
    if data is None:
        return None

    return json.loads(data if isinstance(data, str) else data.decode("utf-8"))


def encode_data(data):
    if data is None:
        return None

    return bytes(json.dumps(data), "utf-8")


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all invalid submissions
    subs = cur.execute("SELECT * FROM submissions").fetchall()

    for d in subs:
        data = decode_data(d["data"])
        d["blocked"] = data is not None and "note" in data
        if d["blocked"]:
            d["reason"] = data["note"]


    # add blocked_items table
    cur.execute("""
        CREATE TABLE blocked_items (
            id INTEGER PRIMARY KEY,
            client_id    INTEGER NOT NULL,
            target_id    INTEGER NOT NULL,
            dataset_id    INTEGER NOT NULL,
            game_id    INTEGER NOT NULL,
            timestamp    INTEGER NOT NULL,
            reason  TEXT DEFAULT NULL,
            UNIQUE(client_id,target_id),
            FOREIGN KEY (client_id) REFERENCES client_info (id) ON DELETE CASCADE
        )"""
    )

    blocked = [s for s in subs if s["blocked"]]
    # insert invalid submissions as blocked items
    cur.executemany(
        "INSERT INTO blocked_items (client_id, target_id, dataset_id, game_id, timestamp, reason) " +
        "VALUES (:client_id, :target_id, :dataset_id, :game_id, :timestamp, :reason);",
        blocked,
    )

    # delete invalid submissions
    cur.executemany("DELETE FROM submissions WHERE id = ?;", [(s["id"],) for s in blocked])

    # commit changes
    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all invalid submissions (blocked items)
    blocked = cur.execute("SELECT * FROM blocked_items").fetchall()

    # delete blocked_items table
    cur.execute("DELETE FROM blocked_items")
    cur.execute("DROP TABLE blocked_items")

    for d in blocked:
        d["data"] = encode_data({ "note": d["reason"] })

    # insert blocked items as submissions
    cur.executemany(
        "INSERT INTO submissions (id, dataset_id, target_id, game_id, client_id, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :game_id, :client_id, :timestamp, :data);",
        blocked
    )

    # commit changes
    connection.commit()
