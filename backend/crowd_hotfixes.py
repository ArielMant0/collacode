import config
import os
import sqlite3
from collections import namedtuple
from pathlib import Path

import app.crowd_wrapper as cw
from table_constants import *

EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    config.EVIDENCE_PATH
)
TEASER_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    config.TEASER_PATH
)

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)

def add_missing_similarities():
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.CROWD_DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    all_clients = cw.get_clients(cur)
    # get all crowd worker clients
    clients = [c for c in all_clients if c["cwId"] is not None]

    for c in clients:
        # get all submissions made by this crowd worker
        subs = cw.get_submissions_by_client_dataset(cur, c["id"], 1, True)
        for sub in subs:
            sid = sub["id"]
            new_subs = []

            high = [s for s in sub["similar"] if s["value"] > 1 and s["source"] < 5]
            normal = [s for s in sub["similar"] if s["value"] == 1 and s["source"] < 5]

            for i in range(0, len(high)):

                tid = high[i]["item_id"]

                for j in range(i+1, len(high)):
                    new_subs.append({
                        "submission_id": sid,
                        "target_id": tid,
                        "item_id": high[j]["item_id"],
                        "value": 2,
                        "source": 5
                    })

                for j in range(0, len(normal)):
                    new_subs.append({
                        "submission_id": sid,
                        "target_id": tid,
                        "item_id": normal[j]["item_id"],
                        "value": 2,
                        "source": 5
                    })

            for ns in new_subs:
                cw.add_similarity(cur, ns, 1)

            # n = len(high)
            # m = len(normal)
            # print(count, n, m, (n*(n-1))/2 + n*m)

    con.commit()


def calculate_item_counts():
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.CROWD_DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    sims = cw.get_similarities_by_dataset(cur, 1)

    values = {}
    counts = {}

    for s in sims:
        item = s["item_id"]
        target = s["target_id"]
        src = s["source"]

        if not target in counts:
            counts[target] = {}
            values[target] = {}

        if not item in counts[target]:
            counts[target][item] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }
            values[target][item] = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 }

        counts[target][item][src] += 1
        values[target][item][src] += s["value"]

    cur.execute("DELETE FROM item_sim_counts")

    rows = []
    now = cw.get_millis()

    for target, other in counts.items():
        for item, cv in other.items():
            obj = {
                "dataset_id": 1,
                "target_id": int(target),
                "item_id": int(item),
                "count": 0,
                "value": 0,
                "last_update": now
            }

            for i in range(1, 6):
                obj["count"] += cv[i]
                obj["count_"+str(i)] = cv[i]
                obj["value"] += values[target][item][i]
                obj["value_"+str(i)] = values[target][item][i]
            rows.append(obj)

    cur.executemany(
        "INSERT INTO item_sim_counts (dataset_id, target_id, item_id, value, value_1, value_2, " +
        "value_3, value_4, value_5, count, count_1, count_2, count_3, count_4, count_5, " +
        "last_update) VALUES (:dataset_id, :target_id, :item_id, :value, :value_1, :value_2, " +
        ":value_3, :value_4, :value_5, :count, :count_1, :count_2, :count_3, :count_4, " +
        ":count_5, :last_update)",
        rows
    )
    con.commit()


if __name__ == "__main__":
    # calculate_item_counts()
    add_missing_similarities()

