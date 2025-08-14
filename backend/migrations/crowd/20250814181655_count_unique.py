"""
This module contains a Caribou migration.

Migration Name: count_unique
Migration Version: 20250814181655
"""

from datetime import datetime, timezone

def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

C_TBL_SIMS = "item_sim_counts"
C_TBL_SUBS = "submissions"
C_TBL_ITEM_SIMS = "item_sims"

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # delete similarity table
    cur.execute(f"DELETE FROM {C_TBL_SIMS}")
    cur.execute(f"DROP TABLE {C_TBL_SIMS}")

    # modify item similarity table
    cur.execute(f"""
        CREATE TABLE {C_TBL_SIMS} (
            id INTEGER PRIMARY KEY,
            dataset_id	INTEGER NOT NULL CHECK(dataset_id > 0),
            target_id	INTEGER NOT NULL CHECK(target_id > 0),
            item_id	INTEGER NOT NULL CHECK(item_id > 0),
            unique_clients  INTEGER DEFAULT 0,
            unique_submissions  INTEGER DEFAULT 0,
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
            UNIQUE(dataset_id,item_id,target_id)
        )"""
    )

    # get all existing submissions and recalculate shit
    sims = cur.execute(f"SELECT * FROM {C_TBL_ITEM_SIMS}").fetchall()

    now = get_millis()
    counts = {}
    start = {
        "dataset_id": 1,
        "count": 0,
        "count_1": 0,
        "count_2": 0,
        "count_3": 0,
        "count_4": 0,
        "count_5": 0,
        "value": 0,
        "value_1": 0,
        "value_2": 0,
        "value_3": 0,
        "value_4": 0,
        "value_5": 0,
        "last_update": now
    }


    for s in sims:

        sub = cur.execute(
            f"SELECT client_id FROM {C_TBL_SUBS} WHERE id = ?",
            (s["submission_id"],)
        ).fetchone()

        if sub is None:
            continue

        smaller = min(s["item_id"], s["target_id"])
        bigger = max(s["item_id"], s["target_id"])

        if smaller not in counts:
            counts[smaller] = {}

        if bigger not in counts[smaller]:
            counts[smaller][bigger] = start.copy()
            counts[smaller][bigger]["clients"] = set()
            counts[smaller][bigger]["submissions"] = set()

        ss = "_" + str(s["source"])
        counts[smaller][bigger]["value"] += s["value"]
        counts[smaller][bigger]["value"+ss] += s["value"]
        counts[smaller][bigger]["count"] += 1
        counts[smaller][bigger]["count"+ss] += 1

        counts[smaller][bigger]["clients"].add(sub["client_id"])
        counts[smaller][bigger]["submissions"].add(s["submission_id"])

    rows = []

    for sid, obj1 in counts.items():
        for bid, obj2 in obj1.items():
            obj2["target_id"] = sid
            obj2["item_id"] = bid
            obj2["unique_clients"] = len(obj2["clients"])
            obj2["unique_submissions"] = len(obj2["submissions"])
            rows.append(obj2)

    cur.executemany(f"""
        INSERT INTO {C_TBL_SIMS} (
            dataset_id,
            target_id,
            item_id,
            unique_clients, unique_submissions,
            value, value_1, value_2, value_3, value_4, value_5,
            count, count_1, count_2, count_3, count_4, count_5,
            last_update
        )
        VALUES (
            :dataset_id,
            :target_id,
            :item_id,
            :unique_clients, :unique_submissions,
            :value, :value_1, :value_2, :value_3, :value_4, :value_5,
            :count, :count_1, :count_2, :count_3, :count_4, :count_5,
            :last_update
        );""",
        rows
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all existing similarity counts
    sims = cur.execute(f"SELECT * FROM {C_TBL_SIMS}").fetchall()

    # delete similarity table
    cur.execute(f"DELETE FROM {C_TBL_SIMS}")
    cur.execute(f"DROP TABLE {C_TBL_SIMS}")

    # modify item similarity table
    cur.execute(f"""
        CREATE TABLE {C_TBL_SIMS} (
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
            UNIQUE(dataset_id,item_id,target_id)
        )"""
    )

    cur.executemany(f"""
        INSERT INTO {C_TBL_SIMS} (
            id,
            dataset_id,
            target_id,
            item_id,
            value, value_1, value_2, value_3, value_4, value_5,
            count, count_1, count_2, count_3, count_4, count_5,
            last_update
        )
        VALUES (
            :id,
            :dataset_id,
            :target_id,
            :item_id,
            :value, :value_1, :value_2, :value_3, :value_4, :value_5,
            :count, :count_1, :count_2, :count_3, :count_4, :count_5,
            :last_update
        );""",
        sims
    )

    connection.commit()

