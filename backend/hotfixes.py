import config
import os
import sqlite3
from collections import namedtuple
from pathlib import Path

import app.db_wrapper as dbw
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


def set_cluster(oldcode, newcode):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    oldexts = cur.execute(
        "SELECT e.*, eg.game_id FROM externalizations e LEFT JOIN ext_groups eg ON e.group_id = eg.id WHERE eg.code_id = ?;",
        (oldcode,),
    ).fetchall()
    newexts = cur.execute(
        "SELECT e.*, eg.game_id FROM externalizations e LEFT JOIN ext_groups eg ON e.group_id = eg.id WHERE eg.code_id = ?;",
        (newcode,),
    ).fetchall()

    for e in newexts:
        old_e = [
            ex
            for ex in oldexts
            if ex["name"] == e["name"]
            and ex["description"] == e["description"]
            and ex["game_id"] == e["game_id"]
        ]
        if len(old_e) > 0:
            old = old_e[0]

            game = cur.execute("SELECT * FROM games WHERE id = ?;", (e["game_id"],)).fetchone()
            print(
                f"seting cluster for {e['name']} ({game['name']}) from {e['cluster']} to {old['cluster']}"
            )

            cur.execute(
                "UPDATE externalizations SET cluster = ? WHERE id = ?;", (old["cluster"], e["id"])
            )

    con.commit()


def hotfix():
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    assigns = cur.execute("SELECT * FROM tag_assignments;").fetchall()
    deleted = 0
    updated = 0

    for d in assigns:
        changes = False
        if (
            d["old_tag"]
            and cur.execute("SELECT 1 FROM tags WHERE id = ?;", (d["old_tag"],)).fetchone() is None
        ):
            d["old_tag"] = None
            changes = True
        if (
            d["new_tag"]
            and cur.execute("SELECT 1 FROM tags WHERE id = ?;", (d["new_tag"],)).fetchone() is None
        ):
            d["new_tag"] = None
            changes = True

        if d["old_tag"] is None and d["new_tag"] is None:
            cur.execute("DELETE FROM tag_assignments WHERE id = ?;", (d["id"],))
            deleted += 1
        elif changes:
            cur.execute(
                "UPDATE tag_assignments SET old_tag = ?, new_tag = ? WHERE id = ?;",
                (d["old_tag"], d["new_tag"], d["id"]),
            )
            updated += 1

    print(f"updated: {updated}, deleted: {deleted}")

    con.commit()


def remove_tags(names):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = namedtuple_factory

    for name in names:
        tags = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE name = ?;", (name,)).fetchall()
        idx = 0
        ids = set()

        print(f"tag: {name}")
        while idx < len(tags):
            t = tags[idx]
            ids.add(t.id)
            children = cur.execute(
                f"SELECT * FROM {TBL_TAGS} WHERE parent = ?;", (t.id,)
            ).fetchall()
            dbw.delete_tags(cur, [c.id for c in children] + [t.id])
            print(f"\tremoved {cur.rowcount} tags")
            tags = tags + children
            idx += 1

    con.commit()


def copy_meta_items(fromCode, toCode):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    mg = dbw.get_meta_groups_by_code(cur, fromCode)
    mi = dbw.get_meta_items_by_code(cur, fromCode)
    cats = dbw.get_meta_categories_by_code(cur, fromCode)

    now = dbw.get_millis()

    changes = True
    assCats = {}

    cur.row_factory = namedtuple_factory
    # add meta catgegories
    while changes:

        changes = False

        for c in cats:
            if c["id"] in assCats or (c["parent"] is not None and c["parent"] not in assCats):
                continue

            nc = c.copy()
            id = nc["id"]
            del nc["id"]
            nc["code_id"] = toCode
            nc["created"] = now
            if c["parent"] is not None:
                nc["parent"] = assCats[c["parent"]]

            ncid = dbw.add_meta_category_return_id(cur, nc)
            assCats[id] = ncid
            changes = True

    cur.row_factory = dict_factory

    tas = dbw.get_tag_assignments_by_codes(cur, fromCode, toCode)
    tagAssO = {t["old_tag"]: t["new_tag"] for t in tas}

    ev = dbw.get_evidence_by_code(cur, fromCode)
    evAss = {}

    for e in ev:
        ta = tagAssO[e["tag_id"]] if e["tag_id"] is not None else None
        en = cur.execute(
            f"SELECT id FROM {TBL_EVIDENCE} WHERE item_id = ? AND created_by = ? AND tag_id = ? AND code_id = ? AND filepath = ? AND description = ?;",
            (e["item_id"], e["created_by"], ta, toCode, e["filepath"], e["description"]),
        ).fetchone()

        # evidence does not exists
        if en is None:
            eid = cur.execute(
                f"INSERT INTO {TBL_EVIDENCE} (item_id, created_by, tag_id, code_id, filepath, description, created) VALUES (?,?,?,?,?,?,?) RETURNING id;",
                (e["item_id"], e["created_by"], ta, toCode, e["filepath"], e["description"], now),
            ).fetchone()
            evAss[e["id"]] = eid["id"]
        else:
            evAss[e["id"]] = en["id"]

    conCat = dbw.get_meta_cat_conns_by_code(cur, fromCode)
    conTag = dbw.get_meta_tag_conns_by_code(cur, fromCode)
    conEv = dbw.get_meta_ev_conns_by_code(cur, fromCode)
    ag = dbw.get_meta_agreements_by_code(cur, fromCode)

    cur.row_factory = namedtuple_factory
    # add meta groups
    for g in mg:
        ng = g.copy()
        del ng["id"]
        ng["code_id"] = toCode
        ng["created"] = now
        # add group
        ngid = dbw.add_meta_group_return_id(cur, ng)

        items = [i for i in mi if i["group_id"] == g["id"]]
        for i in items:
            ni = i.copy()
            del ni["id"]
            ni["group_id"] = ngid
            ni["created"] = now
            ni["tags"] = [d.copy() for d in conTag if d["meta_id"] == i["id"]]
            ni["evidence"] = [d.copy() for d in conEv if d["meta_id"] == i["id"]]
            ni["categories"] = [d.copy() for d in conCat if d["meta_id"] == i["id"]]

            for d in ni["tags"]:
                del d["meta_id"]
                del d["id"]
                d["tag_id"] = tagAssO[d["tag_id"]]

            for d in ni["evidence"]:
                del d["meta_id"]
                del d["id"]
                d["ev_id"] = evAss[d["ev_id"]]

            for d in ni["categories"]:
                del d["meta_id"]
                del d["id"]
                d["cat_id"] = assCats[d["cat_id"]]

            niid = dbw.add_meta_item_return_id(cur, ni)

            if niid is not None:
                agree = [d for d in ag if d["meta_id"] == i["id"]]
                for d in agree:
                    d["meta_id"] = niid
                    del d["id"]
                dbw.add_meta_agreements(cur, agree)

    con.commit()

def reset_invalid_evidence(code):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    ev = cur.execute(f"SELECT * FROM {TBL_EVIDENCE} WHERE code_id = ? AND tag_id IS NOT NULL;", (code,)).fetchall()

    changed = 0
    for e in ev:
        if e["tag_id"] is not None:
            t = cur.execute(f"SELECT id FROM {TBL_TAGS} WHERE id = ?;", (e["tag_id"],)).fetchone()
            if t is None:
                cur.execute(f"UPDATE {TBL_EVIDENCE} SET tag_id = NULL WHERE id = ?;", (e["id"],))
                changed += 1

    print(f"reset {changed} invalid pieces of evidence")
    con.commit()


def remove_duplicate_evidence(code):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    def same(a, b, key):
        return a[key] == b[key]

    ev = dbw.get_evidence_by_code(cur, code)
    sumAll = 0
    sumItem = {}

    ignore = set()
    todel = set()

    for i in range(0, len(ev)):
        e = ev[i]
        other = [
            ev[j]
            for j in range(i + 1, len(ev))
            if not same(ev[j], e, "id")
            and e["id"] not in ignore
            and ev[j]["id"] not in ignore
            and same(ev[j], e, "item_id")
            and same(ev[j], e, "tag_id")
            and same(ev[j], e, "description")
            and same(ev[j], e, "filepath")
        ]
        if len(other) > 0:
            ignore.add(e["id"])
            for o in other:
                ignore.add(o["id"])
                todel.add(o["id"])

            item = cur.execute(
                f"SELECT * FROM {TBL_ITEMS} WHERE id = ?;", (e["item_id"],)
            ).fetchone()
            if item["name"] not in sumItem:
                sumItem[item["name"]] = []

            sumItem[item["name"]] += other
            sumAll += len(other)

    print(f"{sumAll} duplicate pieces of evidence")

    cur.row_factory = namedtuple_factory
    dbw.delete_evidence(cur, list(todel), EVIDENCE_PATH)
    print(f"deleted {len(todel)} duplicate pieces of evidence")
    con.commit()

def remove_invalid_datatags(code):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    datatags = cur.execute(f"SELECT * FROM {TBL_DATATAGS} WHERE code_id = ?;", (code,)).fetchall()

    todel = []
    for d in datatags:
        if d["tag_id"] is not None:
            t = cur.execute(f"SELECT id FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],)).fetchone()
            if t is None:
                todel.append(d["id"])

    dbw.delete_datatags(cur, todel)
    print(f"deleted {len(todel)} invalid datatags")
    con.commit()

def is_steam_url(url):
    return "store.steampowered.com" in url

def get_steam_id(url):
    if not is_steam_url(url):
        return None

    app_idx = url.find("app/")
    if app_idx < 0:
        return None

    last_idx = url.find("/", app_idx+4)
    if last_idx < 0:
        last_idx = len(url)

    return int(url[app_idx+4:last_idx])

def steam_id_fix(dataset=1):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    items = dbw.get_items_by_dataset(cur, dataset)
    table_name = dbw.get_meta_table(cur, dataset)

    count = 0
    countReset = 0

    for it in items:

        if it["url"] is not None and is_steam_url(it["url"]):
            steamid = get_steam_id(it["url"])
            if steamid is not None and steamid != it["steam_id"]:
                cur.execute(f"UPDATE {table_name} SET steam_id = ? WHERE item_id = ?;", (steamid, it["id"]))
                count += 1
        else:
            cur.execute(f"UPDATE {table_name} SET steam_id = ? WHERE item_id = ?;", (None, it["id"]))
            countReset += 1


    print(f"updated {count} steam ids")
    print(f"reset {countReset} steam ids to None")
    con.commit()

def move_images(fromPath: Path, toPath: Path, dataset=1):
    p = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", config.DATABASE_PATH)
    con = sqlite3.connect(p)
    cur = con.cursor()
    cur.row_factory = dict_factory

    items = dbw.get_items_by_dataset(cur, dataset)
    evidence = dbw.get_evidence_by_dataset(cur, dataset)

    ct = 0
    cte = 0
    ce = 0
    cee = 0

    dsp = str(dataset)

    teaserpath = toPath.joinpath("teaser", dsp)
    evidencepath = toPath.joinpath("evidence", dsp)

    if len(items) > 0:
        if not teaserpath.exists():
            teaserpath.mkdir(parents=True, exist_ok=True)

    print(f"moving from path {fromPath}\n\t{teaserpath}\n\t{evidencepath}")

    for it in items:
        if it["teaser"] is not None:
            try:
                tf = fromPath.joinpath("teaser", it["teaser"])
                tt = teaserpath.joinpath(it["teaser"])
                tf.replace(tt)
                ct += 1
            except:
                cte += 1

    print(f"moved {ct} teaser images")
    if cte > 0:
        print(f"failed to move {cte} teaser images")
    print()

    if len(evidence) > 0:
        if not evidencepath.exists():
            evidencepath.mkdir(parents=True, exist_ok=True)

    for e in evidence:
        if e["filepath"] is not None:
            try:
                ef = fromPath.joinpath("evidence", e["filepath"])
                et = evidencepath.joinpath(e["filepath"])
                ef.replace(et)
                ce += 1
            except:
                cee += 1

    print(f"moved {ce} evidence images")
    if cte > 0:
        print(f"failed to move {cee} evidence images")
    print()

if __name__ == "__main__":
    for i in range(1, 4):
        move_images(
            Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "public").resolve(),
            Path(os.path.dirname(os.path.abspath(__file__))).joinpath("media").resolve(),
            i
        )