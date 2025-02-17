import os
import csv
import json
import sqlite3
from app.calc import get_irr_score
import db_wrapper as dbw
from table_constants import *

from pathlib import Path

IGNORE_TAGS = ["camera movement rotation", "camera type", "cutscenes cinematics", "iso perspective"]

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def make_space(length):
    return ",".join(["?"] * length)

def get_ignore_tags(cur):
    result = cur.execute(f"SELECT id FROM {TBL_TAGS} WHERE name IN ({make_space(len(IGNORE_TAGS))});", IGNORE_TAGS).fetchall()
    resultAll = cur.execute(f"SELECT id, parent FROM {TBL_TAGS} WHERE parent IS NOT NULL").fetchall()
    ids = [t["id"] for t in result]
    changes = True
    while changes:
        children = [d["id"] for d in resultAll if d["parent"] is not None and d["parent"] in ids and d["id"] not in ids]
        changes = len(children) > 0
        for child in children:
            ids.append(child)
    return ids

def filter_ignore(cur, data, attr="id"):
    excluded = get_ignore_tags(cur)
    return [d for d in data if d[attr] not in excluded]

def write_json(file, rows):
    json.dump(rows, file, separators=(',', ':'))

def export_json(dbpath, outpath, dataset=None):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    if dataset is None:
        allds = cur.execute(f"SELECT id FROM {TBL_DATASETS};").fetchall()

        users = cur.execute(f"SELECT id, name, role, email FROM {TBL_USERS};").fetchall()
        datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS};", (ds,)).fetchall()

        codes = []
        code_transitions = []
        prj_users = []
        items = []
        expertise = []
        tags = []
        tag_assignments = []
        datatags = []
        evidence = []
        meta_groups = []
        meta_categories = []
        meta_items = []
        meta_agree = []
        meta_cats = []
        meta_tags = []
        meta_evs = []

        for ds in allds:
            codes += dbw.get_codes_by_dataset(cur, ds)
            code_transitions += dbw.get_code_transitions_by_dataset(cur, ds)
            prj_users += dbw.get_users_by_dataset(cur, ds)
            items += dbw.get_items_by_dataset(cur, dataset)
            expertise += dbw.get_item_expertise_by_dataset(cur, ds)
            tags += dbw.get_tags_by_dataset(cur, ds)
            tag_assignments += dbw.get_tag_assignments_by_dataset(cur, ds)
            datatags += dbw.get_datatags_by_dataset(cur, ds)
            evidence += dbw.get_evidence_by_dataset(cur, ds)
            meta_groups += dbw.get_meta_groups_by_dataset(cur, ds)
            meta_categories += dbw.get_meta_categories_by_dataset(cur, ds)
            meta_items += dbw.get_meta_items_by_dataset(cur, ds)
            meta_agree += dbw.get_meta_agreements_by_dataset(cur, ds)
            meta_cats += dbw.get_meta_cat_conns_by_dataset(cur, ds)
            meta_tags += dbw.get_meta_tag_conns_by_dataset(cur, ds)
            meta_evs += dbw.get_meta_ev_conns_by_dataset(cur, ds)
    else:
        datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)).fetchall()
        codes = dbw.get_codes_by_dataset(cur, dataset)
        code_transitions = dbw.get_code_transitions_by_dataset(cur, dataset)
        prj_users = dbw.get_users_by_dataset(cur, dataset)
        users = [
            cur.execute(f"SELECT id, name, role, email FROM {TBL_USERS} WHERE id = ?;", (u["id"],)).fetchone() for u in prj_users
        ]
        items = dbw.get_items_by_dataset(cur, dataset)
        expertise = dbw.get_item_expertise_by_dataset(cur, dataset)
        tags = dbw.get_tags_by_dataset(cur, dataset)
        tag_assignments = dbw.get_tag_assignments_by_dataset(cur, dataset)
        datatags = dbw.get_datatags_by_dataset(cur, dataset)
        evidence = dbw.get_evidence_by_dataset(cur, dataset)
        meta_groups = dbw.get_meta_groups_by_dataset(cur, dataset)
        meta_categories = dbw.get_meta_categories_by_dataset(cur, dataset)
        meta_items = dbw.get_meta_items_by_dataset(cur, dataset)
        meta_agree = dbw.get_meta_agreements_by_dataset(cur, dataset)
        meta_cats = dbw.get_meta_cat_conns_by_dataset(cur, dataset)
        meta_tags = dbw.get_meta_tag_conns_by_dataset(cur, dataset)
        meta_evs = dbw.get_meta_ev_conns_by_dataset(cur, dataset)

    dir = Path(outpath)
    dir.mkdir(exist_ok=True)

    irrTags = []
    irrItems = []

    for c in codes:
        res = get_irr_score(
            prj_users,
            dbw.get_items_merged_by_code(cur, c["id"]),
            [t for t in tags if t["is_leaf"] == 1 and t["code_id"] == c["id"]]
        )
        for r in res["tags"]:
            r["code_id"] = c["id"]
        for r in res["items"]:
            r["code_id"] = c["id"]

        irrTags = irrTags + res["tags"]
        irrItems = irrItems + res["items"]

    with open(dir.joinpath("irr_tags.json"), "w", encoding="utf-8") as file:
        write_json(file, irrTags)
    with open(dir.joinpath("irr_items.json"), "w", encoding="utf-8") as file:
        write_json(file, irrItems)

    with open(dir.joinpath("datasets.json"), "w", encoding="utf-8") as file:
        write_json(file, datasets)

    with open(dir.joinpath("codes.json"), "w", encoding="utf-8") as file:
        write_json(file, codes)

    with open(dir.joinpath("code_transitions.json"), "w", encoding="utf-8") as file:
        write_json(file, code_transitions)

    with open(dir.joinpath("global_users.json"), "w", encoding="utf-8") as file:
        write_json(file, users)

    with open(dir.joinpath("users.json"), "w", encoding="utf-8") as file:
        write_json(file, prj_users)

    with open(dir.joinpath("items.json"), "w", encoding="utf-8") as file:
        write_json(file, items)

    with open(dir.joinpath("item_expertise.json"), "w", encoding="utf-8") as file:
        write_json(file, expertise)

    with open(dir.joinpath("tags.json"), "w", encoding="utf-8") as file:
        write_json(file, tags)

    with open(dir.joinpath("tag_assignments.json"), "w", encoding="utf-8") as file:
        write_json(file, tag_assignments)

    with open(dir.joinpath("datatags.json"), "w", encoding="utf-8") as file:
        write_json(file, datatags)

    with open(dir.joinpath("evidence.json"), "w", encoding="utf-8") as file:
        write_json(file, evidence)

    with open(dir.joinpath("meta_groups.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_groups)

    with open(dir.joinpath("meta_items.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_items)

    with open(dir.joinpath("meta_categories.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_categories)

    with open(dir.joinpath("meta_cat_connections.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_cats)

    with open(dir.joinpath("meta_tag_connections.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_tags)

    with open(dir.joinpath("meta_ev_connections.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_evs)

    with open(dir.joinpath("meta_agreements.json"), "w", encoding="utf-8") as file:
        write_json(file, meta_agree)

def write_csv(file, rows):
    if len(rows) == 0:
        return

    fieldnames = rows[0].keys()
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

def export_csv(dbpath, outpath, dataset=None):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    if dataset is None:
        allds = cur.execute(f"SELECT id FROM {TBL_DATASETS};").fetchall()

        users = cur.execute(f"SELECT id, name, role, email FROM {TBL_USERS};").fetchall()
        datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS};", (ds,)).fetchall()

        codes = []
        code_transitions = []
        prj_users = []
        items = []
        expertise = []
        tags = []
        tag_assignments = []
        datatags = []
        evidence = []
        meta_groups = []
        meta_categories = []
        meta_items = []
        meta_agree = []
        meta_cats = []
        meta_tags = []
        meta_evs = []

        for ds in allds:
            codes += dbw.get_codes_by_dataset(cur, ds)
            code_transitions += dbw.get_code_transitions_by_dataset(cur, ds)
            prj_users += dbw.get_users_by_dataset(cur, ds)
            items += dbw.get_items_by_dataset(cur, dataset)
            expertise += dbw.get_item_expertise_by_dataset(cur, ds)
            tags += dbw.get_tags_by_dataset(cur, ds)
            tag_assignments += dbw.get_tag_assignments_by_dataset(cur, ds)
            datatags += dbw.get_datatags_by_dataset(cur, ds)
            evidence += dbw.get_evidence_by_dataset(cur, ds)
            meta_groups += dbw.get_meta_groups_by_dataset(cur, ds)
            meta_categories += dbw.get_meta_categories_by_dataset(cur, ds)
            meta_items += dbw.get_meta_items_by_dataset(cur, ds)
            meta_agree += dbw.get_meta_agreements_by_dataset(cur, ds)
            meta_cats += dbw.get_meta_cat_conns_by_dataset(cur, ds)
            meta_tags += dbw.get_meta_tag_conns_by_dataset(cur, ds)
            meta_evs += dbw.get_meta_ev_conns_by_dataset(cur, ds)
    else:
        datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)).fetchall()
        codes = dbw.get_codes_by_dataset(cur, dataset)
        code_transitions = dbw.get_code_transitions_by_dataset(cur, dataset)
        prj_users = dbw.get_users_by_dataset(cur, dataset)
        users = [
            cur.execute(f"SELECT id, name, role, email FROM {TBL_USERS} WHERE id = ?;", (u["id"],)).fetchone() for u in prj_users
        ]
        items = dbw.get_items_by_dataset(cur, dataset)
        expertise = dbw.get_item_expertise_by_dataset(cur, dataset)
        tags = dbw.get_tags_by_dataset(cur, dataset)
        tag_assignments = dbw.get_tag_assignments_by_dataset(cur, dataset)
        datatags = dbw.get_datatags_by_dataset(cur, dataset)
        evidence = dbw.get_evidence_by_dataset(cur, dataset)
        meta_groups = dbw.get_meta_groups_by_dataset(cur, dataset)
        meta_categories = dbw.get_meta_categories_by_dataset(cur, dataset)
        meta_items = dbw.get_meta_items_by_dataset(cur, dataset)
        meta_agree = dbw.get_meta_agreements_by_dataset(cur, dataset)
        meta_cats = dbw.get_meta_cat_conns_by_dataset(cur, dataset)
        meta_tags = dbw.get_meta_tag_conns_by_dataset(cur, dataset)
        meta_evs = dbw.get_meta_ev_conns_by_dataset(cur, dataset)

    dir = Path(outpath)
    dir.mkdir(exist_ok=True)

    irrTags = []
    irrItems = []

    for c in codes:
        res = get_irr_score(
            prj_users,
            dbw.get_items_merged_by_code(cur, c["id"]),
            [t for t in tags if t["is_leaf"] == 1 and t["code_id"] == c["id"]]
        )
        for r in res["tags"]:
            r["code_id"] = c["id"]
        for r in res["items"]:
            r["code_id"] = c["id"]

        irrTags = irrTags + res["tags"]
        irrItems = irrItems + res["items"]

    with open(dir.joinpath("irr_tags.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, irrTags)
    with open(dir.joinpath("irr_items.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, irrItems)

    with open(dir.joinpath("datasets.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, datasets)

    with open(dir.joinpath("codes.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, codes)

    with open(dir.joinpath("code_transitions.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, code_transitions)

    with open(dir.joinpath("global_users.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, users)

    with open(dir.joinpath("users.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, prj_users)

    with open(dir.joinpath("items.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, items)

    with open(dir.joinpath("item_expertise.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, expertise)

    with open(dir.joinpath("tags.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, tags)

    with open(dir.joinpath("tag_assignments.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, tag_assignments)

    with open(dir.joinpath("datatags.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, datatags)

    with open(dir.joinpath("evidence.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, evidence)

    with open(dir.joinpath("meta_groups.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_groups)

    with open(dir.joinpath("meta_items.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_items)

    with open(dir.joinpath("meta_categories.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_categories)

    with open(dir.joinpath("meta_cat_connections.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_cats)

    with open(dir.joinpath("meta_tag_connections.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_tags)

    with open(dir.joinpath("meta_ev_connections.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_evs)

    with open(dir.joinpath("meta_agreements.csv"), "w", newline='', encoding="utf-8") as file:
        write_csv(file, meta_agree)

if __name__ == "__main__":
    export_json("./data/data.db", "../public/data", 1)
    # export_csv("./data/data.db", "./exports")