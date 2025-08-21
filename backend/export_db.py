import csv
import json
import os
import config
import sqlite3
from pathlib import Path

import app.db_wrapper as dbw
from app.calc import get_irr_score
from table_constants import (
    TBL_DATASETS,
    TBL_USERS,
)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def make_space(length):
    return ",".join(["?"] * length)


def write_json(file, rows):
    json.dump(rows, file, separators=(",", ":"))


def write_csv(file, rows):
    if len(rows) == 0:
        return

    fieldnames = rows[0].keys()
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)


def write_file(fileType, dir, filename, rows):
    if fileType == "csv":
        with open(dir.joinpath(f"{filename}.{fileType}"), "w", encoding="utf-8", newline="") as file:
            write_csv(file, rows)
    else:
        with open(dir.joinpath(f"{filename}.{fileType}"), "w", encoding="utf-8") as file:
            write_json(file, rows)


def export(outpath, dataset=None, fileType="json"):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    if dataset is None:
        print(f"exporting all datasets to {outpath} as {fileType}")
        users = cur.execute(f"SELECT id, name, role, email FROM {TBL_USERS};").fetchall()
        allds = [d["id"] for d in cur.execute(f"SELECT id FROM {TBL_DATASETS};").fetchall()]

        datasets = dbw.get_datasets(cur)
        codes = []
        code_transitions = []
        prj_users = []
        items = []
        items_finalized = []
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
        game_scores = []
        game_scores_items = []
        game_scores_tags = []
        objections = []

        for ds in allds:
            codes += dbw.get_codes_by_dataset(cur, ds)
            code_transitions += dbw.get_code_transitions_by_dataset(cur, ds)
            prj_users += dbw.get_users_by_dataset(cur, ds)
            items += dbw.get_items_by_dataset(cur, ds)
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
            game_scores += dbw.get_game_scores_by_dataset(cur, ds)
            game_scores_items += dbw.get_game_scores_items_by_dataset(cur, ds)
            game_scores_tags += dbw.get_game_scores_tags_by_dataset(cur, ds)
            objections += dbw.get_objections_by_dataset(cur, ds)
            items_finalized += dbw.get_items_finalized_by_dataset(cur, ds)
    else:
        print(f"exporting dataset {dataset} to {outpath} as {fileType}")
        datasets = cur.execute(
            f"SELECT * FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)
        ).fetchall()
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
        game_scores = dbw.get_game_scores_by_dataset(cur, dataset)
        game_scores_items = dbw.get_game_scores_items_by_dataset(cur, dataset)
        game_scores_tags = dbw.get_game_scores_tags_by_dataset(cur, dataset)
        objections = dbw.get_objections_by_dataset(cur, dataset)
        items_finalized = dbw.get_items_finalized_by_dataset(cur, dataset)

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

    write_file(fileType, dir, "irr_tags", irrTags)
    write_file(fileType, dir, "irr_items", irrItems)
    write_file(fileType, dir, "datasets", datasets)
    write_file(fileType, dir, "codes", codes)
    write_file(fileType, dir, "code_transitions", code_transitions)
    write_file(fileType, dir, "global_users", users)
    write_file(fileType, dir, "users", prj_users)
    write_file(fileType, dir, "items", items)
    write_file(fileType, dir, "item_expertise", expertise)
    write_file(fileType, dir, "items_finalized", items_finalized)
    write_file(fileType, dir, "tags", tags)
    write_file(fileType, dir, "tag_assignments", tag_assignments)
    write_file(fileType, dir, "datatags", datatags)
    write_file(fileType, dir, "evidence", evidence)
    write_file(fileType, dir, "meta_groups", meta_groups)
    write_file(fileType, dir, "meta_items", meta_items)
    write_file(fileType, dir, "meta_categories", meta_categories)
    write_file(fileType, dir, "meta_cat_connections", meta_cats)
    write_file(fileType, dir, "meta_tag_connections", meta_tags)
    write_file(fileType, dir, "meta_ev_connections", meta_evs)
    write_file(fileType, dir, "meta_agreements", meta_agree)
    write_file(fileType, dir, "game_scores", game_scores)
    write_file(fileType, dir, "game_scores_items", game_scores_items)
    write_file(fileType, dir, "game_scores_tags", game_scores_tags)
    write_file(fileType, dir, "objections", objections)

if __name__ == "__main__":
    for i in [1, 2, 3]:
        p = Path(f"../public/data/{i}")
        p.mkdir(parents=True, exist_ok=True)
        export(str(p), i, "csv")
