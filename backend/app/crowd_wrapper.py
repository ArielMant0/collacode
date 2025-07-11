import json
from datetime import datetime, timezone

from table_constants import C_TBL_SIMS, C_TBL_COUNTS


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_similar_count_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE dataset_id = ? GROUP BY target_id;",
        (dataset,)
    ).fetchall()


def get_similar_count_by_target(cur, target):
    return cur.execute(f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? ORDER BY count DESC;", (target,)).fetchall()


def get_similar_count_by_item(cur, item):
    return cur.execute(f"SELECT * FROM {C_TBL_COUNTS} WHERE item_id = ? ORDER BY count DESC;", (item,)).fetchall()


def get_similar_count_by_target_item(cur, target, item):
    return cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? AND item_id = ?;",
        (target, item)
    ).fetchone()


def add_similar_count(cur, dataset, target, item, value):
    existing = get_similar_count_by_target_item(cur, target, item)
    if existing is None:
        cur.execute(
            f"INSERT INTO {C_TBL_COUNTS} (dataset_id, target_id, item_id, count, last_update) VALUES (?,?,?,?,?);",
            (dataset, target, item, value, get_millis()),
        )
    else:
        tmp = existing if isinstance(existing, dict) else existing._asdict()
        tmp["count"] += value
        tmp["last_update"] = get_millis()
        cur.execute(
            f"UPDATE {C_TBL_COUNTS} SET count = ?, last_update = ? WHERE id = ?;",
            (tmp["count"], tmp["last_update"], tmp["id"]),
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
            f"INSERT INTO {C_TBL_SIMS} (dataset_id, target_id, item_id, game_id, guid, timestamp, value, data) VALUES (?,?,?,?,?,?,?,?);",
            (d["dataset_id"], d["target_id"], d["item_id"], d["game_id"], d["guid"], d["timestamp"], d["value"], d["data"]),
        )

        add_similar_count(cur, d["dataset_id"], d["target_id"], d["item_id"], d["value"])

    return cur


def delete_similarity(cur, ids):
    if len(ids) == 0:
        return cur

    return cur.executemany(f"DELETE FROM {C_TBL_SIMS} WHERE id = ?;", [(id,) for id in ids])