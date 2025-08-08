import json
import os
from datetime import datetime, timezone
from numpy.random import random
from pathlib import Path
from uuid import uuid4

from table_constants import (
    C_TBL_BLOCKD,
    C_TBL_CLIENT,
    C_TBL_COUNTS,
    C_TBL_FEED,
    C_TBL_RATINGS,
    C_TBL_SIMS,
    C_TBL_SUBS,
    C_TBL_USERS
)

CW_MAX_SUB = 3
COMP_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", "crowd_comp.json").resolve()
ID_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "data", "crowd_items.json").resolve()

def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def decode_data(data):
    if data is None:
        return None

    return json.loads(data if isinstance(data, str) else data.decode("utf-8"))


def encode_data(data):
    if data is None:
        return None

    return bytes(json.dumps(data), "utf-8")


def get_ratings_by_client(cur, client):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_RATINGS} WHERE client_id = ?;",
        (client["id"],)
    ).fetchone()

    values = {
        "ease": None,
        "fun": None,
        "satisfaction": None,
        "preference": None,
    }

    if res is None:
        return values

    if res["rating_ease"] is not None:
        values["ease"] = res["rating_ease"]
    if res["rating_fun"] is not None:
        values["fun"] = res["rating_fun"]
    if res["rating_satisfaction"] is not None:
        values["satisfaction"] = res["rating_satisfaction"]
    if res["rating_preference"] is not None:
        values["preference"] = res["rating_preference"]

    return values


def get_ratings_counts(cur):
    res = cur.execute(f"SELECT * FROM {C_TBL_RATINGS};").fetchall()
    counts = {
        "ease": { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
        "fun": { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
        "satisfaction": { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
        "preference": { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 },
    }

    for d in res:
        if d["rating_ease"] is not None:
            counts["ease"][d["rating_ease"]] += 1
        if d["rating_fun"] is not None:
            counts["fun"][d["rating_fun"]] += 1
        if d["rating_satisfaction"] is not None:
            counts["satisfaction"][d["rating_satisfaction"]] += 1
        if d["rating_preference"] is not None:
            counts["preference"][d["rating_preference"]] += 1

    return counts


def add_ratings(cur, client, ratings):

    if client is None:
        return cur

    now = get_millis()

    ex = cur.execute(
        f"SELECT * FROM {C_TBL_RATINGS} WHERE client_id = ?;",
        (client["id"],)
    ).fetchone()

    if ex is None:
        cur.execute(
            f"INSERT INTO {C_TBL_RATINGS} (client_id, rating_ease, rating_fun, " +
            "rating_satisfaction, rating_preference, timestamp) VALUES (?,?,?,?,?,?);",
            (
                client["id"],
                ratings["ease"],
                ratings["fun"],
                ratings["satisfaction"],
                ratings["preference"],
                now
            )
        )
    else:
        ex["rating_ease"] = ratings["ease"]
        ex["rating_fun"] = ratings["fun"]
        ex["rating_satisfaction"] = ratings["satisfaction"]
        ex["rating_preference"] = ratings["preference"]
        cur.execute(
            f"UPDATE {C_TBL_RATINGS} SET rating_ease = ?, rating_fun = ?, " +
            "rating_satisfaction = ?, rating_preference = ? WHERE id = ?;",
            (
                ex["rating_ease"],
                ex["rating_fun"],
                ex["rating_satisfaction"],
                ex["rating_preference"],
                ex["id"]
            )
        )

    return cur


def add_feedback(cur, client, text):

    if client is None:
        return cur

    now = get_millis()
    cur.execute(
        f"INSERT INTO {C_TBL_FEED} (client_id, text, timestamp) VALUES (?, ?, ?);",
        (client["id"], text, now)
    )

    return cur


def get_comprehension_check(item_id, delete_answers=False):
    if item_id is None:
        return []

    questions = []

    with open(COMP_PATH, "r") as file:
        data = json.load(file)
        for item in data:
            if item["id"] == item_id:
                questions = item["questions"]
                if delete_answers:
                    for q in questions:
                        del q["answer"]
                return questions

    return questions


def test_comprehension_check(item, answers):
    if item is None:
        return False

    data = get_comprehension_check(item)
    if len(data) == 0:
        return True

    num_correct = 0
    for i, d in enumerate(data):
        if answers[i] == d["answer"]:
            num_correct += 1

    return num_correct > 0 and num_correct / len(data) >= 0.5


def get_available_items(dataset):
    id_list = []

    if dataset == 1:
        with open(ID_PATH, "r") as file:
            id_list = json.load(file)

    return id_list


def get_excluded_tags(dataset):
    if dataset == 1:
        return [
            "mech: other",
            "vis: other",
            "vis: bars",
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
            "ord: branches",
            "ord: linear",
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


def is_client_blocked(client):
    if client is None:
        return False

    return client["requests_recent"] >= 60 or client["attention_fails"] >= 5


def is_crowd_worker_done(cur, client, dataset_id):
    if client is None or dataset_id is None:
        return False

    submitted = client["cwSubmitted"] == 1
    count = get_submissions_count_by_client_dataset(cur, client["id"], dataset_id)
    return client["cwId"] is not None and not submitted and count >= CW_MAX_SUB


def set_crowd_worker_submitted(cur, client):
    if client["cwId"] is not None and client["cwSubmitted"] == 0:
        cur.execute(f"UPDATE {C_TBL_CLIENT} SET cwSubmitted = ? WHERE id = ?;", (1,client["id"]))
        return True

    return False

def get_client_items_by_dataset(cur, client, dataset):
    subs = get_submissions_by_client_dataset(cur, client, dataset)
    blocked = cur.execute(
        f"SELECT * FROM {C_TBL_BLOCKD} WHERE client_id = ? AND dataset_id = ?;",
        (client, dataset)
    )

    nope = set([b["target_id"] for b in blocked])
    done = set([s["target_id"] for s in subs if s["target_id"] not in nope])

    return done, nope


def get_client(cur, client_id, guid, ip=None, cw_id=None):
    if (client_id is None or guid is None) and cw_id is None:
        return None

    client = None


    if cw_id is not None:
        return get_client_by_cw(cur, cw_id)
    elif client_id is not None:
        client = get_client_by_id(cur, cw_id)
        # try to get the client using guid
        if client is None and guid is not None:
            client = get_client_by_guid_ip(cur, guid, ip)
        elif client is not None and guid is not None and client["guid"] != guid:
            client = None
    elif guid is not None:
        client = get_client_by_guid_ip(cur, guid, ip)
    elif ip is not None:
        client = get_client_by_ip(cur, ip)

    # return none (if there is a cw id attached but not passed)
    # so that a new client is created
    if cw_id is None and client is not None and client["cwId"] is not None:
        return None

    return client


def get_client_update(cur, client_id, guid, ip=None, cw_id=None, cw_src=None):
    client = get_client(cur, client_id, guid, ip, cw_id)
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
    res = None

    if ip is not None:
        res = cur.execute(
            f"SELECT * FROM {C_TBL_CLIENT} WHERE guid = ? AND ip = ? ORDER BY last_update DESC;",
            (guid,ip)
        ).fetchone()

    return get_client_by_guid(cur, guid) if res is None else res


def get_client_by_id(cur, id):
    return cur.execute(
        f"SELECT * FROM {C_TBL_CLIENT} WHERE id = ?;",
        (id,)
    ).fetchone()


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

    now = get_millis()
    method = get_next_method(cur, cw_id is not None, dataset)
    obj = {
        "guid": guid,
        "ip": ip,
        "cwId": cw_id,
        "cwSource": cw_src,
        "cwSubmitted": 0,
        "method": method,
        "requests_recent": 1,
        "attention_fails": 0,
        "comprehension_fails": 0,
        "recent_update": now,
        "last_update": now
    }

    res = cur.execute(
        "INSERT INTO client_info (guid, ip, cwId, cwSource, cwSubmitted, method, " +
        "requests_recent, recent_update, last_update) VALUES (:guid, :ip, :cwId, :cwSource, " +
        ":cwSubmitted, :method, :requests_recent, :recent_update, :last_update) " +
        "RETURNING id;",
        obj
    ).fetchone()

    obj["id"] = res["id"]

    return obj


def update_client_info(cur, client, ip):
    if client is None:
        return cur

    now = get_millis()
    last = client["recent_update"]
    # if we are in the latest update window of 30 seconds, update the counter
    if now - last <= 30000:
        client["last_update"] = now
        client["requests_recent"] += 1
    else:
        client["last_update"] = now
        client["recent_update"] = now
        client["requests_recent"] = 1

    if ip is not None and ("ip" not in client or client["ip"] is None):
        client["ip"] = ip

    # update client info
    cur.execute(
        f"UPDATE {C_TBL_CLIENT} SET last_update = ?, recent_update = ?, requests_recent = ?, " +
        "ip = ? WHERE id = ?;",
        (
            client["last_update"],
            client["recent_update"],
            client["requests_recent"],
            client["ip"],
            client["id"]
        )
    )


def update_client_attention_fails(cur, client_id):
    return cur.execute(
        f"UPDATE {C_TBL_CLIENT} SET attention_fails = attention_fails + 1 WHERE id = ?;",
        (client_id,)
    )


def update_client_comprehension_fails(cur, client_id):
    return cur.execute(
        f"UPDATE {C_TBL_CLIENT} SET comprehension_fails = comprehension_fails + 1 WHERE id = ?;",
        (client_id,)
    )


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


def get_similarity_counts_for_targets(cur, targets, target_only=True):

    asdict = {}
    for id in targets:

        if target_only:
            result = cur.execute(
                f"SELECT count FROM {C_TBL_COUNTS} WHERE target_id = ?;",
                (id,)
            ).fetchall()
        else:
            result = cur.execute(
                f"SELECT count FROM {C_TBL_COUNTS} WHERE target_id = ? OR item_id = ?;",
                (id,id)
            ).fetchall()

        asdict[id] = 0
        for r in result:
            asdict[id] += r["count"]

    return asdict

def add_similar_count(cur, dataset, target, item, source, value):

    if target == item:
        return

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


def process_submission(submission):
    if submission is None:
        return None

    submission["data"] = decode_data(submission["data"])
    return submission

def process_submissions(submissions):
    if submissions is None:
        return []

    return [process_submission(s) for s in submissions]


def get_submission(cur, id):
    res = cur.execute(f"SELECT * FROM {C_TBL_SUBS} WHERE id = ?;", (id,)).fetchone()
    return process_submission(res)


def get_submissions_by_guid_dataset(cur, guid, dataset):
    res = cur.execute(
        f"SELECT s.* FROM {C_TBL_SUBS} s LEFT JOIN {C_TBL_CLIENT} c ON s.client_id = c.id WHERE c.guid = ? AND s.dataset_id = ?;",
        (guid, dataset)
    ).fetchall()

    return process_submissions(res)


def get_submissions_by_client_dataset(cur, client_id, dataset_id):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE client_id = ? AND dataset_id = ?;",
        (client_id, dataset_id)
    ).fetchall()

    return process_submissions(res)


def get_submissions_count_by_client_dataset(cur, client_id, dataset_id):
    return len(get_submissions_by_client_dataset(cur, client_id, dataset_id))


def get_submission_counts_by_targets(cur, targets):
    return [get_submission_count_by_target(cur, t) for t in targets]


def get_submission_count_by_target(cur, target):
    result = cur.execute(
        f"SELECT COUNT(*) as count FROM {C_TBL_SUBS} WHERE target_id = ?;",
        (target,)
    ).fetchone()

    if result is None:
        return 0

    return result["count"] if isinstance(result, dict) else result[0]


def get_submission_by_client_target(cur, client, target):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE client_id = ? AND target_id = ?;",
        (client, target)
    ).fetchone()

    return process_submission(res)


def add_blocked_item(cur, client_id, target_id, data, note):
    # check if this user already submitted a similarity
    ex = get_submission_by_client_target(
        cur,
        client_id,
        target_id
    )

    if ex is not None:
        print("cannot block item, submission already exists")
        return cur

    if "dataset_id" not in data or "game_id" not in data:
        print("cannot block item, missing data")
        return cur

    data["client_id"] = client_id
    data["target_id"] = target_id
    data["timestamp"] = get_millis()
    data["reason"] = note

    return cur.execute(
        f"INSERT INTO {C_TBL_BLOCKD} (client_id, target_id, dataset_id, game_id, timestamp, reason) " +
        "VALUES (:client_id, :target_id, :dataset_id, :game_id, :timestamp, :reason);",
        data
    )


def add_submission_return_id(cur, client, data, sims):
    now = get_millis()

    if client is None:
        raise Exception("submission without existing client")

    ip = None

    if "data" not in data:
        data["data"] = None
    else:
        ip = data["data"]["ip"]
        data["data"] = encode_data(data["data"])

    if "timestamp" not in data:
        data["timestamp"] = now

    ds_id = data["dataset_id"]

    if ds_id is None:
        raise Exception("missing dataset id")

    # assign client id
    client_id = client["id"]
    target_id = data["target_id"]
    data["client_id"] = client_id

    # check if this user already submitted a similarity
    ex = get_submission_by_client_target(
        cur,
        client_id,
        target_id
    )

    if ex is not None:
        raise Exception("submission for this user + target already exists")

    # if the client is a crowd worker, check if they already submitted the max
    if client["cwId"] is not None:
        if is_crowd_worker_done(cur, client, ds_id):
            raise Exception("crowd worker is already finished")

    # update client (number of requests and so on)
    update_client_info(cur, client, ip)

    # insert submission
    res = cur.execute(
        f"INSERT INTO {C_TBL_SUBS} (dataset_id, target_id, game_id, client_id, timestamp, data) " +
        "VALUES (:dataset_id, :target_id, :game_id, :client_id, :timestamp, :data) " +
        "RETURNING id",
        data,
    ).fetchone()

    sub_id = res["id"] if isinstance(res, dict) else res[0]
    # add similarity judgements
    for s in sims:
        s["submission_id"] = sub_id
        add_similarity(cur, s)

    return sub_id


def add_submission_return_count(cur, client, data, sims):
    sub_id = add_submission_return_id(cur, client, data, sims)
    sub = get_submission(cur, sub_id)
    if sub is None:
        return 0

    client_id = client["id"]
    dataset_id = sub["dataset_id"]
    return get_submissions_count_by_client_dataset(cur, client_id, dataset_id)


def add_submission(cur, client, data, sims):
    return add_submission_return_id(cur, client, data, sims)


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

    if d["target_id"] == d["item_id"]:
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


def get_dataset_by_similarity(cur, id):
    res = cur.execute(f"SELECT dataset_id FROM {C_TBL_SIMS} WHERE id = ?;", (id,)).fetchone()
    if res is None:
        return None
    return res["dataset_id"] if isinstance(res, dict) else res[0]