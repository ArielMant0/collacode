"""
This module contains a Caribou migration.

Migration Name: logs
Migration Version: 20250720193424
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing similarities
    sims = cur.execute("SELECT * FROM item_sims").fetchall()

    groups = {}
    # group similarities by game + target + guid
    for s in sims:
        gr = s["game_id"]
        target = s["target_id"]
        user = s["guid"]
        if target not in groups:
            groups[target] = {}
        if gr not in groups[target]:
            groups[target][gr] = {}
        if user not in groups[target][gr]:
            groups[target][gr][user] = []

        groups[target][gr][user].append(s)

    subId = 1
    subs = []
    # create new log entries
    for target, pergame in groups.items():
        for game, peruser in pergame.items():
            for guid, data in peruser.items():
                subs.append({
                    "id": subId,
                    "dataset_id": data[0]["dataset_id"],
                    "target_id": target,
                    "game_id": game,
                    "guid": guid,
                    "timestamp": data[0]["timestamp"],
                    "data": None,
                })

                for d in data:
                    d["submission_id"] = subId

                subId += 1

    # add submission log table
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

    # delete similarity table
    cur.execute("DELETE FROM item_sims")
    cur.execute("DROP TABLE item_sims")

    # modify item similarity table
    cur.execute("""
        CREATE TABLE item_sims (
            id INTEGER PRIMARY KEY,
            submission_id	INTEGER NOT NULL CHECK(submission_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            source	INTEGER NOT NULL,
            value	INTEGER NOT NULL,
            UNIQUE(submission_id,target_id,item_id),
            FOREIGN KEY (submission_id) REFERENCES submissions (id) ON DELETE CASCADE
        )"""
    )

    # insert submissions
    cur.executemany(
        "INSERT INTO submissions (id, dataset_id, target_id, game_id, guid, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :game_id, :guid, :timestamp, :data);",
        subs,
    )

    # insert modified similarities
    cur.executemany(
        "INSERT INTO item_sims (id, submission_id, target_id, item_id, source, value) " +
        "VALUES (:id, :submission_id, :target_id, :item_id, :source, :value);",
        sims,
    )

    # commit changes
    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing similarities and submissions
    subs = cur.execute("SELECT * FROM submissions").fetchall()

    sims = []
    for sub in subs:
        sim_list = cur.execute("SELECT * FROM item_sims WHERE submission_id = ?", (sub["id"],)).fetchall()
        for s in sim_list:
            s["dataset_id"] = sub["dataset_id"]
            s["target_id"] = sub["target_id"]
            s["game_id"] = sub["game_id"]
            s["guid"] = sub["guid"]
            s["timestamp"] = sub["timestamp"]
            s["data"] = sub["data"]

    # delete tables
    cur.execute("DELETE FROM item_sims")
    cur.execute("DROP TABLE item_sims")
    cur.execute("DELETE FROM submissions")
    cur.execute("DROP TABLE submissions")

    # modify item similarity table
    cur.execute("""
        CREATE TABLE item_sims (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            guid	TEXT NOT NULL,
            game_id	INTEGER NOT NULL,
            source	INTEGER NOT NULL,
            value	INTEGER NOT NULL,
            timestamp	INTEGER NOT NULL,
            data	BLOB,
            UNIQUE(target_id,item_id,guid,game_id,source)
        )"""
    )

    # insert modified similarities
    cur.executemany(
        "INSERT INTO item_sims (id, dataset_id, target_id, item_id, guid, game_id, source, value, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :guid, :game_id, :source, :value, :timestamp, :data);",
        sims,
    )

    # commit changes
    connection.commit()
