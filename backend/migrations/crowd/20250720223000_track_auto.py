"""
This module contains a Caribou migration.

Migration Name: track_auto
Migration Version: 20250720223000
"""

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing similarity counts
    sims = cur.execute("SELECT * FROM item_sim_counts").fetchall()
    for s in sims:
        s["value_5"] = 0
        s["count_5"] = 0

    # delete similarity table
    cur.execute("DELETE FROM item_sim_counts")
    cur.execute("DROP TABLE item_sim_counts")

    # modify item similarity table
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
            value_5	INTEGER DEFAULT 0,
            count	INTEGER NOT NULL,
            count_1	INTEGER DEFAULT 0,
            count_2	INTEGER DEFAULT 0,
            count_3	INTEGER DEFAULT 0,
            count_4	INTEGER DEFAULT 0,
            count_5	INTEGER DEFAULT 0,
            last_update	INTEGER NOT NULL,
            UNIQUE(item_id,target_id)
        )"""
    )

    # insert modified similarities
    cur.executemany(
        "INSERT INTO item_sim_counts (id, dataset_id, target_id, item_id, value, value_1, value_2, " +
        "value_3, value_4, value_5, count, count_1, count_2, count_3, count_4, count_5, last_update) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :value, :value_1, :value_2, :value_3, " +
        ":value_4, :value_5, :count, :count_1, :count_2, :count_3, :count_4, :count_5, :last_update);",
        sims,
    )

    # commit changes
    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing similarity counts
    sims = cur.execute("SELECT * FROM item_sim_counts").fetchall()

    # delete similarity table
    cur.execute("DELETE FROM item_sim_counts")
    cur.execute("DROP TABLE item_sim_counts")

    # modify item similarity table
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

    # insert modified similarities
    cur.executemany(
        "INSERT INTO item_sim_counts (id, dataset_id, target_id, item_id, value, value_1, value_2, " +
        "value_3, value_4, count, count_1, count_2, count_3, count_4, last_update) " +
        "VALUES (:id, :dataset_id, :target_id, :item_id, :value, :value_1, :value_2, :value_3, " +
        ":value_4, :count, :count_1, :count_2, :count_3, :count_4, :last_update);",
        sims,
    )

    # commit changes
    connection.commit()

