"""
This module contains a Caribou migration.

Migration Name: track_source
Migration Version: 20250720152651
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing data
    sim_counts = cur.execute("SELECT * FROM item_sim_counts").fetchall()
    sims = cur.execute("SELECT * FROM item_sims").fetchall()

    # add new fields for aggregate stuff
    for s in sim_counts:
        s["value"] = s["count"]
        s["value_1"] = s["value"]
        s["value_2"] = 0
        s["value_3"] = 0
        s["value_4"] = 0
        s["count"] = len([1 for d in sims if d["target_id"] == s["target_id"] and d["item_id"] == s["item_id"]])
        s["count_1"] = s["count"]
        s["count_2"] = 0
        s["count_3"] = 0
        s["count_4"] = 0

    # add new fields for single submissions
    for s in sims:
        s["source"] = 1

    # delete existing tables
    cur.execute("DELETE FROM item_sim_counts;")
    cur.execute("DROP TABLE item_sim_counts;")
    cur.execute("DELETE FROM item_sims;")
    cur.execute("DROP TABLE item_sims;")

    # modify tables
    cur.execute("""
        CREATE TABLE item_sim_counts (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            value	INTEGER NOT NULL,
            value_1	INTEGER DEFAULT 0,
            value_2	INTEGER DEFAULT 0,
            value_3	INTEGER DEFAULT 0,
            value_4	INTEGER DEFAULT 0,
            count	INTEGER NOT NULL,
            count_1	INTEGER DEFAULT 0,
            count_2	INTEGER DEFAULT 0,
            count_3	INTEGER DEFAULT 0,
            count_4	INTEGER DEFAULT 0,
            last_update	INTEGER NOT NULL,
            UNIQUE(item_id,target_id)
        )"""
    )

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

    cur.execute("""
        CREATE TABLE user_guids (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            user_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            guid	TEXT NOT NULL,
            UNIQUE(user_id,guid)
        )"""
    )

    # insert data again
    cur.executemany(
        "INSERT INTO item_sim_counts (id, dataset_id, target_id, item_id, value, value_1, " +
        "value_2, value_3, value_4, count, count_1, count_2, count_3, count_4, last_update) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :value, :value_1, :value_2, :value_3, " +
        ":value_4, :count, :count_1, :count_2, :count_3, :count_4, :last_update);",
        sim_counts,
    )

    cur.executemany(
        "INSERT INTO item_sims (id, dataset_id, target_id, item_id, guid, game_id, source, value, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :guid, :game_id, :source, :value, :timestamp, :data);",
        sims,
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing data
    sim_counts = cur.execute("SELECT * FROM item_sim_counts").fetchall()
    sims = cur.execute("SELECT * FROM item_sims").fetchall()

    # reset fields for aggregate stuff
    for s in sim_counts:
        s["count"] = s["value"]

    # delete existing tables
    cur.execute("DELETE FROM item_sim_counts;")
    cur.execute("DROP TABLE item_sim_counts;")
    cur.execute("DELETE FROM item_sims;")
    cur.execute("DROP TABLE item_sims;")
    cur.execute("DELETE FROM user_guids;")
    cur.execute("DROP TABLE user_guids;")

    # reset tables
    cur.execute("""
        CREATE TABLE item_sim_counts (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            count	INTEGER NOT NULL,
            last_update	INTEGER NOT NULL,
            UNIQUE(item_id,target_id)
        )"""
    )

    cur.execute("""
        CREATE TABLE item_sims (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            guid	TEXT NOT NULL,
            game_id	INTEGER NOT NULL,
            value	INTEGER NOT NULL,
            timestamp	INTEGER NOT NULL,
            data	BLOB,
            UNIQUE(target_id,item_id,guid,game_id)
        )"""
    )

    # insert data again
    cur.executemany(
        "INSERT INTO item_sim_counts (id, dataset_id, target_id, item_id, count, last_update) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :count, :last_update);",
        sim_counts,
    )

    cur.executemany(
        "INSERT INTO item_sims (id, dataset_id, target_id, item_id, guid, game_id, value, timestamp, data) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :guid, :game_id, :value, :timestamp, :data);",
        sims,
    )

    connection.commit()