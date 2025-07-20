import json
from datetime import datetime, timezone
from uuid import uuid4

from table_constants import C_TBL_SIMS, C_TBL_COUNTS, C_TBL_USERS


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def guid_exists(cur, guid):
    return cur.execute(
        f"SELECT 1 FROM {C_TBL_SIMS} WHERE guid = ? LIMIT 1;",
        (guid,)
    ).fetchone() is not None


def get_new_guid(cur):
    guid = str(uuid4())
    iter = 0
    while guid_exists(cur, guid) and iter < 50:
        guid = str(uuid4())
        iter += 1
    return guid


def user_exists(cur, id):
    return cur.execute(
        f"SELECT 1 FROM {C_TBL_USERS} WHERE user_id = ? LIMIT 1;",
        (id,)
    ).fetchone() is not None


def get_users(cur):
    return cur.execute(f"SELECT * FROM {C_TBL_USERS};").fetchall()


def get_users_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT * FROM {C_TBL_USERS} WHERE dataset_id = ?;",
        (dataset,)
    ).fetchall()


def get_user_guid(cur, user_id):
    res = cur.execute(
        f"SELECT guid FROM {C_TBL_USERS} WHERE user_id = ?;",
        (user_id,)
    ).fetchone()

    if res is not None:
        return res["guid"] if isinstance(res, dict) else res[0]

    return None


def add_users(cur, data):
    if len(data) == 0:
        return cur

    for d in data:
        if user_exists(cur, d["user_id"]) or guid_exists(cur, d["guid"]):
            continue

        cur.execute(
            f"INSERT INTO {C_TBL_USERS} (dataset, user_id, guid) VALUES (?,?);",
            (d["dataset"], d["user_id"], d["guid"]),
        )

    return cur


def get_similar_count_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE dataset_id = ?;",
        (dataset,)
    ).fetchall()


def get_similar_count_by_target(cur, target):
    return cur.execute(f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? ORDER BY value DESC;", (target,)).fetchall()


def get_similar_count_by_item(cur, item):
    return cur.execute(f"SELECT * FROM {C_TBL_COUNTS} WHERE item_id = ? ORDER BY value DESC;", (item,)).fetchall()


def get_similar_count_by_target_item(cur, target, item):
    return cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? AND item_id = ?;",
        (target, item)
    ).fetchone()


def add_similar_count(cur, dataset, target, item, source, value):

    # get existing object
    existing = get_similar_count_by_target_item(cur, target, item)

    # values and counts
    v1 = v2 = v3 = v4 = 0
    c1 = c2 = c3 = c4 = 0
    if source == 1:
        v1 = value
        c1 = value
    elif source == 2:
        v2 = value
        c2 = value
    elif source == 3:
        v3 = value
        c3 = value
    elif source == 4:
        v4 = value
        c4 = value

    if existing is None:
        cur.execute(
            f"INSERT INTO {C_TBL_COUNTS} " +
            "(dataset_id, target_id, item_id, value, value_1, value_2, value_3, value_4, " +
            "count, count_1, count_2, count_3, count_4, last_update) VALUES (:dataset_id, " +
            ":target_id, :item_id, :value, :value_1, :value_2, :value_3, :value_4, " +
            ":count, :count_1, :count_2, :count_3, :count_4, :last_update)",
            (
                dataset, target, item,
                value, v1, v2, v3, v4,
                1, c1, c2, c3, c4,
                get_millis()
            ),
        )
    else:
        tmp = existing if isinstance(existing, dict) else existing._asdict()
        tmp["value"] += value
        tmp["value_1"] += v1
        tmp["value_2"] += v2
        tmp["value_3"] += v3
        tmp["value_4"] += v4

        tmp["count"] += 1
        tmp["count_1"] += c1
        tmp["count_2"] += c2
        tmp["count_3"] += c3
        tmp["count_4"] += c4

        tmp["last_update"] = get_millis()
        cur.execute(
            f"UPDATE {C_TBL_COUNTS} SET value = ?, count = ?, last_update = ?, " +
            "value_1 = ?, value_2 = ?, value_3 = ?, value_4 = ?, " +
            "count_1 = ?, count_2 = ?, count_3 = ?, count_4 = ? " +
            "WHERE id = ?;",
            (
                tmp["value"], tmp["count"], tmp["last_update"],
                tmp["value_1"], tmp["value_2"], tmp["value_3"], tmp["value_4"],
                tmp["count_1"], tmp["count_2"], tmp["count_3"], tmp["count_4"],
                tmp["id"]
            ),
        )

    return cur


def get_similarity_by_target_item_game_user(cur, target, item, game, user):
    return cur.execute(
        f"SELECT * FROM {C_TBL_SIMS} WHERE target_id = ? AND item_id = ? AND game_id = ? AND guid = ?;",
        (target, item, game, user)
    ).fetchone()


def add_similarity(cur, data):
    if len(data) == 0:
        return cur

    now = get_millis()
    for d in data:

        if "data" not in d:
            d["data"] = None
        else:
            d["data"] = bytes(json.dumps(d["data"]), "utf-8")

        if "timestamp" not in d:
            d["timestamp"] = now

        if "source" not in d:
            d["source"] = 1

        # check if this user already submitted a similarity
        ex = get_similarity_by_target_item_game_user(
            cur,
            d["target_id"],
            d["item_id"],
            d["game_id"],
            d["guid"],
        )

        if ex is not None:
            print("similarity already exists")
            continue

        cur.execute(
            f"INSERT INTO {C_TBL_SIMS} (dataset_id, target_id, item_id, game_id, guid, source, timestamp, value, data) " +
            "VALUES (:dataset_id, :target_id, :item_id, :game_id, :guid, :source, :timestamp, :value, :data);",
            d,
        )

        add_similar_count(cur, d["dataset_id"], d["target_id"], d["item_id"], d["source"], d["value"])

    return cur


def delete_similarity(cur, ids):
    if len(ids) == 0:
        return cur

    return cur.executemany(f"DELETE FROM {C_TBL_SIMS} WHERE id = ?;", [(id,) for id in ids])