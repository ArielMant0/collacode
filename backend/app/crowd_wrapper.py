import json
from datetime import datetime, timezone
from uuid import uuid4

from table_constants import C_TBL_CLIENT, C_TBL_COUNTS, C_TBL_SIMS, C_TBL_SUBS, C_TBL_USERS


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def is_client_blocked(cur, guid, ip=None):
    result = add_client_info(cur, guid, ip)
    return result["requests_recent"] >= 60

def add_client_info(cur, guid, ip=None):
    if ip is None:
        result = cur.execute(
            f"SELECT * FROM {C_TBL_CLIENT} WHERE guid = ?;",
            (guid,)
        ).fetchone()
    else:
        result = cur.execute(
            f"SELECT * FROM {C_TBL_CLIENT} WHERE guid = ? AND ip = ? ORDER BY recent_update;",
            (guid,ip)
        ).fetchone()

    now = get_millis()

    if result is None:
        obj = {
            "guid": guid,
            "ip": ip,
            "request_count": 1,
            "requests_recent": 1,
            "recent_update": now,
            "last_update": now
        }

        cur.execute(
            "INSERT INTO client_info (guid, ip, request_count, requests_recent, recent_update, last_update) " +
            "VALUES (:guid, :ip, :request_count, :requests_recent, :recent_update, :last_update);",
            obj
        )

        return obj

    last = result["recent_update"]
    # if we are in the latest update window of 30 seconds, update the counter
    if now - last <= 30000:
        result["last_update"] = now
        result["requests_recent"] += 1
        result["request_count"] += 1
    else:
        result["last_update"] = now
        result["recent_update"] = now
        result["requests_recent"] = 1
        result["request_count"] += 1

    if ip is not None and ("ip" not in result or result["ip"] is None):
        result["ip"] = ip

    # update client info
    cur.execute(
        f"UPDATE {C_TBL_CLIENT} SET last_update = ?, recent_update = ?, requests_recent = ?, " +
        "request_count = ?, ip = ? WHERE id = ?;",
        (
            result["last_update"],
            result["recent_update"],
            result["requests_recent"],
            result["request_count"],
            result["ip"],
            result["id"]
        )
    )

    return result


def guid_exists(cur, guid):
    return cur.execute(
        f"SELECT 1 FROM {C_TBL_SUBS} WHERE guid = ? LIMIT 1;",
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
    v1 = v2 = v3 = v4 = v5 = 0
    c1 = c2 = c3 = c4 = c5 = 0

    if source == 1:
        v1 = value
        c1 = 1
    elif source == 2:
        v2 = value
        c2 = 1
    elif source == 3:
        v3 = value
        c3 = 1
    elif source == 4:
        v4 = value
        c4 = 1
    elif source == 5:
        v5 = value
        c5 = 1

    if existing is None:
        cur.execute(
            f"INSERT INTO {C_TBL_COUNTS} " +
            "(dataset_id, target_id, item_id, value, value_1, value_2, value_3, value_4, value_5, " +
            "count, count_1, count_2, count_3, count_4, count_5, last_update) VALUES (:dataset_id, " +
            ":target_id, :item_id, :value, :value_1, :value_2, :value_3, :value_4, :value_5, " +
            ":count, :count_1, :count_2, :count_3, :count_4, :count_5, :last_update)",
            (
                dataset, target, item,
                value, v1, v2, v3, v4, v5,
                1, c1, c2, c3, c4, c5,
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
        tmp["value_5"] += v5

        tmp["count"] += 1
        tmp["count_1"] += c1
        tmp["count_2"] += c2
        tmp["count_3"] += c3
        tmp["count_4"] += c4
        tmp["count_5"] += c5

        tmp["last_update"] = get_millis()
        cur.execute(
            f"UPDATE {C_TBL_COUNTS} SET value = ?, count = ?, last_update = ?, " +
            "value_1 = ?, value_2 = ?, value_3 = ?, value_4 = ?, value_5 = ?, " +
            "count_1 = ?, count_2 = ?, count_3 = ?, count_4 = ?, count_5 = ? " +
            "WHERE id = ?;",
            (
                tmp["value"], tmp["count"], tmp["last_update"],
                tmp["value_1"], tmp["value_2"], tmp["value_3"], tmp["value_4"], tmp["value_5"],
                tmp["count_1"], tmp["count_2"], tmp["count_3"], tmp["count_4"], tmp["count_5"],
                tmp["id"]
            ),
        )

    return cur


def get_dataset_id_from_submission(cur, sub_id):
    res = cur.execute(
        f"SELECT dataset_id FROM {C_TBL_SUBS} WHERE id = ?;",
        (sub_id,)
    ).fetchone()

    if res is not None:
        return res["dataset_id"] if isinstance(res, dict) else res[0]

    return None


def get_submission_by_guid_target_game(cur, guid, target, game):
    return cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE guid = ? AND target_id = ? AND game_id = ?;",
        (guid, target, game)
    ).fetchone()


def add_submission_return_id(cur, data, sims):
    now = get_millis()

    if "guid" not in data:
        print("missing guid for submission")
        return None

    guid = data["guid"]
    ip = None

    if "data" not in data:
        data["data"] = None
    else:
        ip = data["data"]["ip"]
        data["data"] = bytes(json.dumps(data["data"]), "utf-8")

    if "timestamp" not in data:
        data["timestamp"] = now

    # check if this user already submitted a similarity
    ex = get_submission_by_guid_target_game(
        cur,
        guid,
        data["target_id"],
        data["game_id"]
    )

    if ex is not None:
        print("submission for this user + target + game already exists")
        return None

    add_client_info(cur, guid, ip)

    # insert submission
    res = cur.execute(
        f"INSERT INTO {C_TBL_SUBS} (dataset_id, target_id, game_id, guid, timestamp, data) " +
        "VALUES (:dataset_id, :target_id, :game_id, :guid, :timestamp, :data) " +
        "RETURNING id",
        data,
    ).fetchone()

    sub_id = res["id"] if isinstance(res, dict) else res[0]
    # add similarity judgements
    for s in sims:
        s["submission_id"] = sub_id
        add_similarity(cur, s)


def add_submission(cur, data, sims):
    return add_submission_return_id(cur, data, sims)


def delete_submissions(cur, ids):
    if len(ids) == 0:
        return cur

    return cur.executemany(f"DELETE FROM {C_TBL_SUBS} WHERE id = ?;", [(id,) for id in ids])


def get_similarity_by_submission_target_item(cur, submission, target, item):
    return cur.execute(
        f"SELECT * FROM {C_TBL_SIMS} WHERE submission_id = ? AND target_id = ? AND item_id = ?;",
        (submission, target, item)
    ).fetchone()


def add_similarity(cur, d, dataset=None):

    if "submission_id" not in d:
        return cur

    if "source" not in d:
        d["source"] = 1

    # check if this user already submitted a similarity
    ex = get_similarity_by_submission_target_item(
        cur,
        d["submission_id"],
        d["target_id"],
        d["item_id"]
    )

    if ex is not None:
        print("similarity already exists")
        return cur

    cur.execute(
        f"INSERT INTO {C_TBL_SIMS} (submission_id, target_id, item_id, source, value) " +
        "VALUES (:submission_id, :target_id, :item_id, :source, :value);",
        d,
    )

    if dataset is None:
        dataset = get_dataset_id_from_submission(cur, d["submission_id"])

    add_similar_count(cur, dataset, d["target_id"], d["item_id"], d["source"], d["value"])

    return cur


def delete_similarities(cur, ids):
    if len(ids) == 0:
        return cur

    return cur.executemany(f"DELETE FROM {C_TBL_SIMS} WHERE id = ?;", [(id,) for id in ids])