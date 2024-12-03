import sys
import sqlite3

from pathlib import Path

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def hotfix(oldcode, newcode, dbpath="./data/data.db"):
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

if __name__ == "__main__":
    hotfix(sys.argv[1], sys.argv[2])
