import json
import os
import config
from datetime import datetime, timezone
from numpy.random import random
from pathlib import Path
from uuid import uuid4

from table_constants import (
    C_TBL_BLOCKD,
    C_TBL_CLIENT,
    C_TBL_COUNTS,
    C_TBL_FEED,
    C_TBL_INTS,
    C_TBL_RATINGS,
    C_TBL_SIMS,
    C_TBL_SUBS,
    C_TBL_USERS
)

GAME_IDS = [1, 2]
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


def get_feedback_by_client(cur, client_id):
    res = cur.execute(f"SELECT * FROM {C_TBL_FEED} WHERE client_id = ?;", (client_id,)).fetchall()

    feedback = {}
    for gid in GAME_IDS:
        feedback[gid] = ""

    for r in res:
        feedback[r["game_id"]] = r["text"]

    return feedback


def get_ratings(cur):
    return cur.execute(f"SELECT * FROM {C_TBL_RATINGS} WHERE client_id;").fetchall()


def get_ratings_by_client(cur, client_id):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_RATINGS} WHERE client_id = ?;",
        (client_id,)
    ).fetchall()

    ratings = {}
    values = {
        "ease": None,
        "fun": None,
        "satisfaction": None,
        "preference": None,
    }

    for id in GAME_IDS:
        ratings[id] = values.copy()

    if res is None:
        return ratings

    for r in res:
        if r["rating_ease"] is not None:
            ratings[r["game_id"]]["ease"] = r["rating_ease"]
        if r["rating_fun"] is not None:
            ratings[r["game_id"]]["fun"] = r["rating_fun"]
        if r["rating_satisfaction"] is not None:
            ratings[r["game_id"]]["satisfaction"] = r["rating_satisfaction"]
        if r["rating_preference"] is not None:
            ratings[r["game_id"]]["preference"] = r["rating_preference"]

    return ratings


def get_ratings_counts(cur):

    res = cur.execute(
        f"""SELECT
            game_id,
            category,
            rating,
            COUNT(*) AS count
        FROM (
            SELECT
                game_id,
                'ease' AS category,
                rating_ease AS rating
            FROM {C_TBL_RATINGS}
            UNION ALL
            SELECT
                game_id,
                'fun' AS category,
                rating_fun AS rating
            FROM {C_TBL_RATINGS}
            UNION ALL
            SELECT
                game_id,
                'preference' AS category,
                rating_preference AS rating
            FROM {C_TBL_RATINGS}
            UNION ALL
            SELECT
                game_id,
                'satisfaction' AS category,
                rating_satisfaction AS rating
            FROM {C_TBL_RATINGS}
        ) AS unpivoted
        GROUP BY game_id, category, rating
        ORDER BY game_id, category, rating;
        """
    ).fetchall()

    ratings = {}
    counts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
    options = ["ease", "fun", "satisfaction", "preference"]

    for id in GAME_IDS:
        ratings[id] = {}
        for o in options:
            ratings[id][o] = counts.copy()

    for d in res:
        ratings[d["game_id"]][d["category"]][d["rating"]] = d["count"]

    return ratings


def add_ratings(cur, client_id, ratings):

    if client_id is None:
        return cur

    now = get_millis()

    ex = cur.execute(
        f"SELECT * FROM {C_TBL_RATINGS} WHERE client_id = ? AND game_id = ?;",
        (client_id, ratings["game_id"])
    ).fetchone()

    if ex is None:
        cur.execute(
            f"INSERT INTO {C_TBL_RATINGS} (client_id, game_id, rating_ease, rating_fun, " +
            "rating_satisfaction, rating_preference, timestamp) VALUES (?,?,?,?,?,?,?);",
            (
                client_id,
                ratings["game_id"],
                ratings["ease"],
                ratings["fun"],
                ratings["satisfaction"],
                ratings["preference"],
                now
            )
        )

    return cur


def add_feedback(cur, client_id, game_id, text):

    if client_id is None or game_id is None or text is None:
        return cur

    now = get_millis()
    cur.execute(
        f"INSERT INTO {C_TBL_FEED} (client_id, game_id, text, timestamp) VALUES (?,?,?,?);",
        (client_id, game_id, text, now)
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
            "int: new data",
            "int: visual aid",
            "ord: branches",
            "ord: linear",
            "chunk: package wise",
            "chunk: continuous",
            "exp: heterogeneous",
            "exp: homogeneous",
            "dd: arrow indicator"
        ]
    return []


def get_next_method(cur, is_cw):
    if not is_cw:
        return 0


    min15 = 90000
    mintime = get_millis() - min15

    clients = cur.execute(
        f"""SELECT
                c.*, COUNT(s.id) AS sub_count
            FROM {C_TBL_CLIENT} c
            LEFT JOIN {C_TBL_SUBS} s
                ON s.client_id = c.id
            WHERE c.cwId IS NOT NULL
            GROUP BY c.id
            HAVING
                COUNT(s.id) > 0
                OR c.last_update >= ?
        """,
        (mintime,)
    ).fetchall()

    if clients is None or len(clients) == 0:
        return 1 if random() >= 0.5 else 2

    method = 0
    value = None
    counts = {
        1: 0,
        2: 0
    }

    for c in clients:
        if c["method"] > 0:
            counts[c["method"]] += 1

    for i, val in counts.items():
        if value == None or val < value:
            method = i
            value = val

    return method


def is_client_blocked(client):
    if client is None:
        return False

    if client["requests_recent"] >= 60:
        return True

    if client["cwId"] is not None:
        return client["attention_fails"] >= config.CW_MAX_SUB

    return client["attention_fails"] >= 5


def is_crowd_worker_done(cur, client, dataset_id):
    if client is None or dataset_id is None:
        return False

    submitted = client["cwSubmitted"] == 1
    count = get_submissions_count_by_client_dataset(cur, client["id"], dataset_id)
    return client["cwId"] is not None and not submitted and count >= config.CW_MAX_SUB


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


def get_clients(cur):
    return cur.execute(f"SELECT * FROM {C_TBL_CLIENT};").fetchall()


def get_client(cur, client_id, guid, ip=None, cw_id=None):
    if (client_id is None or guid is None) and cw_id is None:
        return None

    client = None

    if cw_id is not None:
        return get_client_by_cw(cur, cw_id)
    elif client_id is not None:
        client = get_client_by_id(cur, client_id)
        if client is not None and (guid is None or client["guid"] != guid):
            # is guid is missing or does not match, do not return this client
            client = None
        elif client is None and guid is not None:
            # try to get the client using only guid
            client = get_client_by_guid_ip(cur, guid, ip)
    elif guid is not None:
        client = get_client_by_guid_ip(cur, guid, ip)

    # return none (if there is a cw id attached but not passed)
    # so that a new client is created
    if cw_id is None and client is not None and client["cwId"] is not None:
        return None

    return client


def get_client_update(cur, client_id, guid, user_src=None, ip=None, cw_id=None):
    client = get_client(cur, client_id, guid, ip, cw_id)
    if client is not None:
        # set the crowd worker id
        if client["cwId"] is None and cw_id is not None:
            client["cwId"] = cw_id

        if client["source"] is None and user_src is not None:
            client["source"] = user_src

        # set the global id
        if client["guid"] is None and guid is not None:
            client["guid"] = guid

        # set the ip address
        if client["ip"] is None and ip is not None:
            client["ip"] = ip

        # update client data
        cur.execute(
            f"UPDATE {C_TBL_CLIENT} SET cwId = ?, source = ?, guid = ?, ip = ? WHERE id = ?;",
            (client["cwId"], client["source"], client["guid"], client["ip"], client["id"])
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
    if id is None:
        return None
    return cur.execute(f"SELECT * FROM {C_TBL_CLIENT} WHERE id = ?;", (int(id),)).fetchone()


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


def get_game_counts_by_client(cur, client_id):
    res = cur.execute(
        f"SELECT game_id, COUNT(game_id) as count FROM {C_TBL_SUBS} WHERE client_id = ? GROUP BY game_id;",
        (client_id,)
    ).fetchall()

    counts = { 1: 0, 2: 0 }
    if res is None:
        return counts

    for r in res:
        counts[r["game_id"]] = r["count"]

    return counts


def get_game_per_item_by_client(cur, client_id):
    res = cur.execute(
        f"SELECT game_id, target_id FROM {C_TBL_SUBS} WHERE client_id = ?;",
        (client_id,)
    ).fetchall()
    return { r["target_id"]: r["game_id"] for r in res}


def client_exists(cur, id):
    return get_client_by_id(cur, id) is not None


def add_client_info(cur, guid, user_src=None, ip=None, cw_id=None):

    if guid is None:
        guid = get_new_guid(cur)

    now = get_millis()
    method = get_next_method(cur, cw_id is not None)
    obj = {
        "guid": guid,
        "ip": ip,
        "cwId": cw_id,
        "source": user_src,
        "cwSubmitted": 0,
        "method": method,
        "requests_recent": 1,
        "attention_fails": 0,
        "comprehension_fails": 0,
        "recent_update": now,
        "last_update": now
    }

    res = cur.execute(
        "INSERT INTO client_info (guid, ip, cwId, source, cwSubmitted, method, " +
        "requests_recent, recent_update, last_update) VALUES (:guid, :ip, :cwId, :source, " +
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


def process_similar_count(cur, counts):
    if counts is None:
        return None

    umap = {}

    for r in counts:
        if r["target_id"] not in umap:
            umap[r["target_id"]] = get_submission_count_unique_by_target(cur, r["target_id"])

        if r["item_id"] not in umap:
            umap[r["item_id"]] = get_submission_count_unique_by_target(cur, r["item_id"])

        r["unique_target"] = umap[r["target_id"]]
        r["unique_item"] = umap[r["item_id"]]

    return counts


def get_similar_count_by_dataset(cur, dataset):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE dataset_id = ? ORDER BY target_id ASC;",
        (dataset,)
    ).fetchall()

    return process_similar_count(cur, res)


def get_similar_count_by_target(cur, target):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? OR item_id = ? ORDER BY value DESC;",
        (target,target)
    ).fetchall()

    return process_similar_count(cur, res)


def get_similar_count_by_target_item(cur, target, item):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_COUNTS} WHERE (target_id = ? AND item_id = ?) "
        "OR (item_id = ? AND target_id = ?);",
        (target, item, target, item)
    ).fetchone()

    return None if res is None else process_similar_count(cur, [res])[0]


def get_similar_items_for_target(cur, target, limit=0, minUnique=1):
    if minUnique > 1:
        res = cur.execute(
            f"SELECT * FROM {C_TBL_COUNTS} WHERE (target_id = ? OR item_id = ?) " +
            "AND unique_clients >= ? ORDER BY count DESC;",
            (target, target, minUnique)
        ).fetchall()
    else:
        res = cur.execute(
            f"SELECT * FROM {C_TBL_COUNTS} WHERE target_id = ? OR item_id = ? "
            "ORDER BY count DESC;",
            (target,target)
        ).fetchall()

    return res[0:limit] if limit > 0 else res


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
        cur.execute(f"""
            INSERT INTO {C_TBL_COUNTS} (
                dataset_id,
                target_id,
                item_id,
                unique_clients, unique_submissions,
                value, value_1, value_2, value_3, value_4, value_5,
                count, count_1, count_2, count_3, count_4, count_5,
                last_update
            ) VALUES (
                :dataset_id,
                :target_id,
                :item_id,
                :unique_clients, :unique_submissions,
                :value, :value_1, :value_2, :value_3, :value_4, :value_5,
                :count, :count_1, :count_2, :count_3, :count_4, :count_5,
                :last_update
            );""",
            (
                dataset,
                target,
                item,
                1, 1,
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

        nunique = get_submission_count_unique_by_target_item(cur, target, item, True)
        nsubs = get_submission_count_by_target_item(cur, target, item, True)

        cur.execute(f"""
            UPDATE {C_TBL_COUNTS} SET
                value = ?, count = ?, last_update = ?,
                unique_clients = ?, unique_submissions = ?,
                value_1 = ?, value_2 = ?, value_3 = ?, value_4 = ?, value_5 = ?,
                count_1 = ?, count_2 = ?, count_3 = ?, count_4 = ?, count_5 = ?
            WHERE id = ?;""",
            (
                tmp["value"], tmp["count"], tmp["last_update"],
                nunique, nsubs,
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


def enrich_submission(cur, submission):
    sub = process_submission(submission)
    if sub:
        sub["similar"] = cur.execute(
            f"SELECT * FROM {C_TBL_SIMS} WHERE submission_id = ? AND target_id = ?;",
            (sub["id"], sub["target_id"])
        ).fetchall()

    return sub


def process_submission(submission):
    if submission is None:
        return None

    submission["data"] = decode_data(submission["data"])
    return submission


def process_submissions(cur, submissions, enrich=False):
    if submissions is None:
        return []

    return [enrich_submission(cur, s) if enrich else process_submission(s) for s in submissions]


def make_space(length):
    return ",".join(["?"] * length)


def get_submissions_by_dataset(cur, dataset, enrich=False):
    subs = cur.execute(f"SELECT * FROM {C_TBL_SUBS} WHERE dataset_id = ?;", (dataset,)).fetchall()
    return process_submissions(cur, subs, enrich)


def get_submissions_by_dataset(cur, dataset, enrich=False):
    subs = cur.execute(f"SELECT * FROM {C_TBL_SUBS} WHERE dataset_id = ?;", (dataset,)).fetchall()
    return process_submissions(cur, subs, enrich)


def get_submissions_by_guid_dataset(cur, guid, dataset, enrich=False):
    res = cur.execute(
        f"SELECT s.* FROM {C_TBL_SUBS} s LEFT JOIN {C_TBL_CLIENT} c ON s.client_id = c.id WHERE c.guid = ? AND s.dataset_id = ?;",
        (guid, dataset)
    ).fetchall()

    return process_submissions(cur, res, enrich)


def get_submissions_by_client_dataset(cur, client_id, dataset_id, enrich=False):
    res = cur.execute(
        f"SELECT * FROM {C_TBL_SUBS} WHERE client_id = ? AND dataset_id = ?;",
        (client_id, dataset_id)
    ).fetchall()

    return process_submissions(cur, res, enrich)


def get_submissions_count_by_client_dataset(cur, client_id, dataset_id):
    return len(get_submissions_by_client_dataset(cur, client_id, dataset_id))


def get_submission_counts(cur):
    obj = {}
    res = cur.execute(
        f"SELECT target_id, COUNT(DISTINCT id) as count FROM {C_TBL_SUBS} GROUP BY target_id;",
    ).fetchall()
    for r in res:
        obj[r["target_id"]] = r["count"]

    return obj


def get_submission_counts_by_targets(cur, targets, allowItem=True):
    obj = {}
    for t in targets:
        try:
            count = get_submission_count_unique_by_target(cur, t, allowItem)
            obj[t] = count
        except Exception as e:
            print(str(e))
            obj[t] = 0

    return obj


def get_submission_count_by_target(cur, target, allowItem=True):

    if allowItem:
        result = cur.execute(
            f"""SELECT COUNT(DISTINCT s.id) as count FROM {C_TBL_SUBS} s
            INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id
            WHERE st.target_id = ? OR st.item_id = ?;""",
            (target, target)
        ).fetchone()
    else:
        result = cur.execute(
            f"SELECT COUNT(*) as count FROM {C_TBL_SUBS} WHERE target_id = ?",
            (target,)
        ).fetchone()

    if result is None:
        return 0

    return result["count"] if isinstance(result, dict) else result[0]


def get_submission_count_unique_by_target(cur, target, allowItem=True):
    if allowItem:
        result = cur.execute(
            f"""SELECT COUNT(DISTINCT c.id) as count FROM {C_TBL_CLIENT} c
            INNER JOIN {C_TBL_SUBS} s ON s.client_id = c.id
            INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id
            WHERE st.target_id = ? OR st.item_id = ?;""",
            (target,target)
        ).fetchone()
    else:
        result = cur.execute(
            f"SELECT COUNT(DISTINCT id) as count FROM {C_TBL_SUBS} WHERE target_id = ?",
            (target,)
        ).fetchone()

    if result is None:
        return 0

    return result["count"] if isinstance(result, dict) else result[0]


def get_submission_count_by_target_item(cur, target, item, bothOrders=True):
    if bothOrders:
        result = cur.execute(
            f"SELECT COUNT(DISTINCT s.id) as count FROM {C_TBL_SUBS} s " +
            f"INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id " +
            f"WHERE st.target_id = ? AND st.item_id = ? " +
            "OR st.item_id = ? AND st.target_id = ?;",
            (target, item, target, item)
        ).fetchone()
    else:
        result = cur.execute(
            f"SELECT COUNT(DISTINCT s.id) as count FROM {C_TBL_SUBS} s " +
            f"INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id " +
            f"WHERE st.target_id = ? AND st.item_id = ?;",
            (target, item)
        ).fetchone()

    if result is None:
        return 0

    return result["count"] if isinstance(result, dict) else result[0]


def get_submission_count_unique_by_target_item(cur, target, item, bothOrders=True):
    if bothOrders:
        result = cur.execute(
            f"SELECT COUNT(DISTINCT c.id) as count FROM {C_TBL_CLIENT} c " +
            f"INNER JOIN {C_TBL_SUBS} s ON s.client_id = c.id " +
            f"INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id " +
            f"WHERE st.target_id = ? AND st.item_id = ? " +
            "OR st.item_id = ? AND st.target_id = ?;",
            (target, item, target, item)
        ).fetchone()
    else:
        result = cur.execute(
            f"SELECT COUNT(DISTINCT c.id) as count FROM {C_TBL_CLIENT} c " +
            f"INNER JOIN {C_TBL_SUBS} s ON s.client_id = c.id " +
            f"INNER JOIN {C_TBL_SIMS} st ON s.id = st.submission_id " +
            f"WHERE st.target_id = ? AND st.item_id = ?;",
            (target, item)
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


def get_similarity_sources(cur):
    return cur.execute(
        f"SELECT source, COUNT(*) as count FROM {C_TBL_SIMS} GROUP BY source;",
    ).fetchall()


def get_similarity_sources_by_dataset(cur, dataset):
    return cur.execute(
        f"""SELECT i.source, COUNT(*) as count FROM {C_TBL_SIMS} i
        JOIN {C_TBL_SUBS} s ON s.id = i.submission_id
        WHERE s.dataset_id = ? GROUP BY source;""",
        (dataset,)
    ).fetchall()


def get_similarity_sources_by_dataset_clients(cur, dataset, ids):
    return cur.execute(
        f"""SELECT i.source, COUNT(*) as count FROM {C_TBL_SIMS} i
        JOIN {C_TBL_SUBS} s ON s.id = i.submission_id
        WHERE s.dataset_id = ? AND s.client_id IN ({make_space(len(ids))})
        GROUP BY source;""",
        [dataset] + ids
    ).fetchall()


def get_similarities(cur):
    return cur.execute(f"SELECT * FROM {C_TBL_SIMS};").fetchall()


def get_similarities_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT s.* FROM {C_TBL_SIMS} s JOIN {C_TBL_SUBS} t ON s.submission_id = t.id "+
        " WHERE t.dataset_id = ?;",
        (dataset,)
    ).fetchall()


def get_similarities_by_target(cur, target):
    return cur.execute(f"SELECT * FROM {C_TBL_SIMS} WHERE target_id = ?;", (target,)).fetchall()


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


def add_interaction_logs(cur, client_id, data):
    if len(data) == 0:
        return cur

    if not client_exists(cur, client_id):
        return cur

    for d in data:
        if "data" not in d:
            d["data"] = None

    cur.executemany(
        f"INSERT INTO {C_TBL_INTS} (client_id, timestamp, action, data) VALUES (?, ?, ?, ?);",
        [(client_id, d["timestamp"], d["action"], d["data"]) for d in data]
    )
