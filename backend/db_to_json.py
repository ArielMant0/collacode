import json
import sqlite3

from pathlib import Path

IGNORE_TAGS = ["camera movement rotation", "camera type", "cutscenes cinematics", "iso perspective"]


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def make_space(length):
    return ",".join(["?"] * length)

def get_ignore_tags(cur):
    result = cur.execute(f"SELECT id FROM tags WHERE name IN ({make_space(len(IGNORE_TAGS))});", IGNORE_TAGS).fetchall()
    resultAll = cur.execute(f"SELECT id, parent FROM tags WHERE parent IS NOT NULL").fetchall()
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

def export_json(dbpath, outpath):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()
    cur.row_factory = dict_factory

    datasets = cur.execute("SELECT * FROM datasets;").fetchall()
    codes = cur.execute("SELECT * FROM codes;").fetchall()
    code_transitions = cur.execute("SELECT * FROM code_transitions;").fetchall()
    users = cur.execute("SELECT id, name, role, dataset_id FROM users;").fetchall()
    users = [u for u in users if u["id"] != 3]
    games = cur.execute("SELECT * FROM games;").fetchall()
    game_expertise = cur.execute("SELECT * FROM game_expertise;").fetchall()
    tags = filter_ignore(cur, cur.execute("SELECT * FROM tags;").fetchall())
    tag_assignments = filter_ignore(cur, cur.execute("SELECT * FROM tag_assignments;").fetchall())
    datatags = filter_ignore(cur, cur.execute("SELECT * FROM datatags;").fetchall())
    evidence = filter_ignore(cur, cur.execute("SELECT * FROM evidence;").fetchall())
    ext_groups = cur.execute("SELECT * FROM ext_groups;").fetchall()
    ext_categories = cur.execute("SELECT * FROM ext_categories;").fetchall()
    exts = cur.execute("SELECT * FROM externalizations;").fetchall()
    ext_agree = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    ext_cats = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_tags = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_evs = cur.execute("SELECT * FROM ext_ev_connections;").fetchall()
    memos = cur.execute("SELECT * FROM memos;").fetchall()

    dir = Path(outpath)
    dir.mkdir(exist_ok=True)

    with open(dir.joinpath("datasets.json"), "w") as file:
        json.dump(datasets, file, separators=(',', ':'))

    with open(dir.joinpath("codes.json"), "w") as file:
        json.dump(codes, file, separators=(',', ':'))

    with open(dir.joinpath("code_transitions.json"), "w") as file:
        json.dump(code_transitions, file, separators=(',', ':'))

    with open(dir.joinpath("users.json"), "w") as file:
        json.dump(users, file, separators=(',', ':'))

    with open(dir.joinpath("games.json"), "w") as file:
        json.dump(games, file, separators=(',', ':'))

    with open(dir.joinpath("game_expertise.json"), "w") as file:
        json.dump(game_expertise, file, separators=(',', ':'))

    with open(dir.joinpath("tags.json"), "w") as file:
        json.dump(tags, file, separators=(',', ':'))

    with open(dir.joinpath("tag_assignments.json"), "w") as file:
        json.dump(tag_assignments, file, separators=(',', ':'))

    with open(dir.joinpath("datatags.json"), "w") as file:
        json.dump(datatags, file, separators=(',', ':'))

    with open(dir.joinpath("evidence.json"), "w") as file:
        json.dump(evidence, file, separators=(',', ':'))

    with open(dir.joinpath("ext_groups.json"), "w") as file:
        json.dump(ext_groups, file, separators=(',', ':'))

    with open(dir.joinpath("externalizations.json"), "w") as file:
        json.dump(exts, file, separators=(',', ':'))

    with open(dir.joinpath("ext_categories.json"), "w") as file:
        json.dump(ext_categories, file, separators=(',', ':'))

    with open(dir.joinpath("ext_cat_connections.json"), "w") as file:
        json.dump(ext_cats, file, separators=(',', ':'))

    with open(dir.joinpath("ext_tag_connections.json"), "w") as file:
        json.dump(ext_tags, file, separators=(',', ':'))

    with open(dir.joinpath("ext_ev_connections.json"), "w") as file:
        json.dump(ext_evs, file, separators=(',', ':'))

    with open(dir.joinpath("ext_agreements.json"), "w") as file:
        json.dump(ext_agree, file, separators=(',', ':'))

    with open(dir.joinpath("memos.json"), "w") as file:
        json.dump(memos, file, separators=(',', ':'))

if __name__ == "__main__":
    export_json("./data/data.db", "../public/data")