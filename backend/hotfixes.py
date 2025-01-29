from collections import namedtuple
import sqlite3
import db_wrapper as dbw
from table_constants import *

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)

def set_cluster(oldcode, newcode, dbpath="./data/data.db"):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    oldexts = cur.execute("SELECT e.*, eg.game_id FROM externalizations e LEFT JOIN ext_groups eg ON e.group_id = eg.id WHERE eg.code_id = ?;", (oldcode,)).fetchall()
    newexts = cur.execute("SELECT e.*, eg.game_id FROM externalizations e LEFT JOIN ext_groups eg ON e.group_id = eg.id WHERE eg.code_id = ?;", (newcode,)).fetchall()

    for e in newexts:
        old_e = [ex for ex in oldexts if ex["name"] == e["name"] and ex["description"] == e["description"] and ex["game_id"] == e["game_id"]]
        if len(old_e) > 0:
            old = old_e[0]

            game = cur.execute("SELECT * FROM games WHERE id = ?;", (e["game_id"],)).fetchone()
            print(f"seting cluster for {e['name']} ({game['name']}) from {e['cluster']} to {old['cluster']}")

            cur.execute("UPDATE externalizations SET cluster = ? WHERE id = ?;", (old["cluster"], e["id"]))

    con.commit()

def hotfix(dbpath="./data/data.db"):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    assigns = cur.execute("SELECT * FROM tag_assignments;").fetchall()
    deleted = 0
    updated = 0

    for d in assigns:
        changes = False
        if d["old_tag"] and cur.execute("SELECT 1 FROM tags WHERE id = ?;", (d["old_tag"],)).fetchone() is None:
            d["old_tag"] = None
            changes = True
        if d["new_tag"] and cur.execute("SELECT 1 FROM tags WHERE id = ?;", (d["new_tag"],)).fetchone() is None:
            d["new_tag"] = None
            changes = True

        if d["old_tag"] is None and d["new_tag"] is None:
            cur.execute("DELETE FROM tag_assignments WHERE id = ?;", (d["id"],))
            deleted += 1
        elif changes:
            cur.execute(
                "UPDATE tag_assignments SET old_tag = ?, new_tag = ? WHERE id = ?;",
                (d["old_tag"], d["new_tag"], d["id"])
            )
            updated += 1

    print(f"updated: {updated}, deleted: {deleted}")

    con.commit()

def remove_tags(names, dbpath="./data/data.db"):
    con = sqlite3.connect(dbpath)
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
            children = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE parent = ?;", (t.id,)).fetchall()
            dbw.delete_tags(cur, [c.id for c in children]+[t.id])
            print(f"\tremoved {cur.rowcount} tags")
            tags = tags + children
            idx += 1

            # # remove tag assignments
            # cur.execute(f"DELETE FROM {TBL_TAG_ASS} WHERE old_tag = ? or new_tag = ?;", (t["id"], t["id"]))
            # print(f"\tremoved {cur.rowcount} tag assignments")

            # # remove evidence connection to tag
            # cur.execute(f"UPDATE {TBL_EVIDENCE} SET tag_id = NULL WHERE tag_id = ?;", (t["id"],))
            # print(f"\tupdated {cur.rowcount} evidence pieces")

            # # remove meta item connection to tag
            # cur.execute(f"DELETE FROM {TBL_META_CON_TAG} WHERE tag_id = ?;", (t["id"],))
            # print(f"\tremoved {cur.rowcount} meta tag connections")

            # # remove tag itself
            # cur.execute(f"DELETE FROM {TBL_TAGS} WHERE id = ?;", (t["id"],))


    con.commit()

if __name__ == "__main__":
    remove_tags(["camera movement rotation", "camera type", "cutscenes cinematics", "iso perspective"])
