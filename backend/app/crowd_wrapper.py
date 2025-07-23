import json
from datetime import datetime, timezone
from numpy.random import random
from uuid import uuid4

from table_constants import C_TBL_CLIENT, C_TBL_COUNTS, C_TBL_SIMS, C_TBL_SUBS, C_TBL_USERS


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def get_available_items(dataset):
    if dataset == 1:
        # return list(range(20, 51))
        return list(range(1, 388))
    return []


def get_excluded_tags(dataset):
    if dataset == 1:
        return [
            "mech: other",
            "vis: other",
            "vision: other",
            "set-g: other",
            "set-s: other",
            "set-t: other",
            "top: other",
            "pc: other",
            "spn: other",
            "info: other",
            "misc: tutorial",
            "int: highlight",
        ]
    return []


def get_submission_counts_by_items(cur, item_ids):
    counts = {}
    for id in item_ids:
        counts[id] = get_submission_count_by_target(cur, id)
    return counts


def get_next_method(cur, is_cw, dataset=None):
    if not is_cw:
        return 0

    if dataset is None:
        counts = cur.execute(
            f"SELECT game_id, COUNT(*) as count FROM {C_TBL_SUBS} GROUP BY game_id;"
        ).fetchall()
    else:
        counts = cur.execute(
            f"SELECT game_id, COUNT(*) as count FROM {C_TBL_SUBS} WHERE dataset_id = ? GROUP BY game_id;",
            (dataset,)
        ).fetchall()

    if counts is None:
        return 1 if random() >= 0.5 else 2

    method = 0
    value = None
    for d in counts:
        if value is None or d["count"] < value:
            value = d["count"]
            method = d["game_id"]

    return method


def is_client_blocked(cur, guid, ip=None):
    result = get_client_by_guid_ip(cur, guid, ip)
    return result is not None and result["requests_recent"] >= 60


def get_client_items_by_dataset(cur, guid, dataset):
    subs = get_submissions_by_guid_dataset(cur, guid, dataset)
    done = set()
    for s in subs:
        done.add(s["target_id"])
    return done


def get_client(cur, guid, ip=None, cw_id=None):
    if guid is None and cw_id is None:
        return None

    client = None

    if cw_id is not None:
        return get_client_by_cw(cur, cw_id)
    elif guid is not None and ip is not None:
        client = get_client_by_guid_ip(cur, guid, ip)
    elif guid is not None and ip is None:
        client = get_client_by_guid(cur, guid)
    elif ip is not None:
        client = get_client_by_ip(cur, ip)

    # return none (if there is a cw id attached but not passed)
    # so that a new client is created
    if cw_id is None and client is not None and client["cwId"] is not None:
        return None

    return client


def get_client_update(cur, guid, ip=None, cw_id=None, cw_src=None):
    client = get_client(cur, guid, ip, cw_id)
    if client is not None:
        # set the crowd worker id
        if client["cwId"] is None and cw_id is not None:
            client["cwId"] = cw_id
            client["cwSource"] = cw_src

        # set the global id
        if client["guid"] is None and guid is not None:
            client["guid"] = guid

        # set the ip address
        if client["ip"] is None and ip is not None:
            client["ip"] = ip

        # update client data
        cur.execute(
            f"UPDATE {C_TBL_CLIENT} SET cwId = ?, cwSource = ?, guid = ?, ip = ? WHERE id = ?;",
            (client["cwId"], client["cwSource"], client["guid"], client["ip"], client["id"])
        )

    return client


def get_client_by_guid_ip(cur, guid, ip=None):
    if ip is not None:
        return cur.execute(
            f"SELECT * FROM {C_TBL_CLIENT} WHERE guid = ? AND ip = ? ORDER BY last_update DESC;",
            (guid,ip)
        ).fetchone()

    return get_client_by_guid(cur, guid)


def get_client_by_guid(cur, guid):
    return cur.execute(
        f"SELECT * FROM {C_TBL_CLIENT} WHERE guid = ? ORDER BY last_update DESC;",
        (guid,)
    ).fetchone()


def get_client_by_cw(cur, cw_id):
    return cur.execute(
        f"SELECT * FROM {C_TBL_CLIENT} WHERE cwId = ?;",
        (cw_id,)
    ).fetchone()


def get_client_by_ip(cur, ip):
    return cur.execute(
        f"SELECT * FROM {C_TBL_CLIENT} WHERE ip = ? ORDER BY last_update DESC;",
        (ip,)
    ).fetchone()


def add_client_info(cur, guid, ip=None, cw_id=None, cw_src=None, dataset=None):

    if guid is None:
        guid = get_new_guid(cur)
    
    result = get_client(cur, guid, ip, cw_id)

    now = get_millis()

    if result is None:
        method = get_next_method(cur, cw_id is not None, dataset)
        obj = {
            "guid": guid,
            "ip": ip,
            "cwId": cw_id,
            "cwSource": cw_src,
            "method": method,
            "requests_recent": 1,
            "recent_update": now,
            "last_update": now
        }

        cur.execute(
            "INSERT INTO client_info (guid, ip, cwId, cwSource, method, requests_recent, recent_update, last_update) " +
            "VALUES (:guid, :ip, :cwId, :cwSource, :method, :requests_recent, :recent_update, :last_update);",
            obj
        )

        return obj

    last = result["recent_update"]
    # if we are in the latest update window of 30 seconds, update the counter
    if now - last <= 30000:
        result["last_update"] = now
        result["requests_recent"] += 1
    else:
        result["last_update"] = now
        result["recent_update"] = now
        result["requests_recent"] = 1

    if ip is not None and ("ip" not in result or result["ip"] is None):
        result["ip"] = ip

    # update client info
    cur.execute(
        f"UPDATE {C_TBL_CLIENT} SET last_update = ?, recent_update = ?, requests_recent = ?, " +
        "ip = ? WHERE id = ?;",
        (
            result["last_update"],
            result["recent_update"],
            result["requests_recent"],
            result["ip"],
            result["id"]
        )
    )

    return result


def guid_exists(cur, guid):
    return cur.execute(
        f"SELECT 1 FROM {C_TBL_CLIENT} WHERE guid = ? ORDER BY last_update DESC LIMIT 1;",
        (guid,)
    ).fetchone() is not None


def get_new_guid(cur):
    guid = str(uuid4())
    iter = 0
    while guid_exists(cur, guid) and iter < 50:
        guid = str(uuid4())
        iter += 1
    return guid


def get_guid_by_ip(cur, ip):
    client = get_client_by_ip(cur, ip)
    return client["guid"] if isinstance(client, dict) else client[0]


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


def get_similarity_counts_for_targets(cur, targets):

    asdict = {}
    for id in targets:

        result = cur.execute(
            f"SELECT count FROM {C_TBL_COUNTS} WHERE target_id = ? OR item_id = ?;",
            (id,id)
        ).fetchall()

        asdict[id] = 0
        for r in result:
            asdict[id] += r["count"]

    return asdict

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


def get_submissions_by_guid_dataset(cur, guid, dataset):
    return cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE guid = ? AND dataset_id = ?;",
        (guid, dataset)
    ).fetchall()


def get_submission_count_by_target(cur, target):
    result = cur.execute(
        f"SELECT COUNT(*) as count FROM {C_TBL_SUBS} WHERE target_id = ?;",
        (target,)
    ).fetchone()
    if result is None:
        return 0
    return result["count"] if isinstance(result, dict) else result[0]


def get_submission_by_guid_target(cur, guid, target):
    return cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE guid = ? AND target_id = ?;",
        (guid, target)
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
    ex = get_submission_by_guid_target(
        cur,
        guid,
        data["target_id"]
    )

    if ex is not None:
        print("submission for this user + target already exists")
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