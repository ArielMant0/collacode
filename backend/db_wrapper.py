import numpy as np
from datetime import datetime, timezone

def make_space(length):
    return ",".join(["?"] * length)

def get_datasets(cur):
    return cur.execute("SELECT * from datasets").fetchall()

def add_dataset(cur, name, description):
    return cur.execute("INSERT INTO datasets (name, description) VALUES (?, ?);", (name, description))

def get_games_by_dataset(cur, dataset):
    return cur.execute("SELECT * from games WHERE dataset_id = ?;", (dataset,)).fetchall()

def add_games(cur, dataset, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], dataset, d["name"], d["year"], d["played"], d["url"], d["teaser"]))
        else:
            rows.append((dataset, d["name"], d["year"], d["played"], d["url"], d["teaser"]))

    stmt = "INSERT INTO games (dataset_id, name, year, played, url, teaser) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO games (id, dataset_id, name, year, played, url, teaser) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_games(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        rows.append((d["name"], d["year"], d["played"], d["url"], d["teaser"], d["id"]))
    return cur.executemany("UPDATE games SET name = ?, year = ?, played = ?, url = ?, teaser = ? WHERE id = ?;", rows)

def delete_games(cur, data, base_path, backup_path):
    if len(data) == 0:
        return cur

    filenames = cur.execute(f"SELECT teaser FROM games WHERE id IN ({make_space(len(data))});", data).fetchall()
    for f in filenames:
        if f[0] is not None:
            base_path.joinpath(f[0]).unlink(missing_ok=True)
            backup_path.joinpath(f[0]).unlink(missing_ok=True)

    return cur.executemany("DELETE FROM games WHERE id = ?;", [(id,) for id in data])

def get_users_by_dataset(cur, dataset):
    return cur.execute("SELECT * from users WHERE dataset_id = ?;", (dataset,)).fetchall()

def add_users(cur, dataset, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], dataset, d["name"], d["role"], d["email"]))
        else:
            rows.append((dataset, d["name"], d["role"], d["email"]))

    stmt = "INSERT INTO users (dataset_id, name, role, email) VALUES (?, ?, ?, ?);" if not with_id else "INSERT INTO users (id, dataset_id, name, role, email) VALUES (?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def get_codes_by_dataset(cur, dataset):
    return cur.execute("SELECT * from codes WHERE dataset_id = ?;", (dataset,)).fetchall()

def add_codes(cur, dataset, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], dataset, d["name"], d["description"], d["created"], d["created_by"]))
        else:
            rows.append((dataset, d["name"], d["description"], d["created"], d["created_by"]))

    stmt = "INSERT INTO codes (dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?);" if not with_id else "INSERT INTO codes (id, dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_codes(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        rows.append((d["name"], d["description"], d["id"]))
    return cur.executemany("UPDATE codes SET name = ?, description = ? WHERE id = ?;", rows)

def get_tags_by_dataset(cur, dataset):
    return cur.execute(
        "SELECT tags.* from tags LEFT JOIN codes ON tags.code_id = codes.id WHERE codes.dataset_id = ?;",
        (dataset,)
    ).fetchall()
def get_tags_by_code(cur, code):
    return cur.execute("SELECT * from tags WHERE code_id = ?;", (code,)).fetchall()

def add_tag_return_id(cur, d):
    cur = cur.execute(
        "INSERT INTO tags (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id;",
        (d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaf"])
    )
    return next(cur)

def add_tag_return_tag(cur, d):
    cur = cur.execute(
        "INSERT INTO tags (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *;",
        (d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaf"])
    )
    return next(cur)

def add_tags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    ids = []
    with_id = "id" in data[0]

    for d in data:
        if "is_leaf" not in d or d["is_leaf"] is None:
            d["is_leaf"] = 1
        if "parent" not in d:
            d["parent"] = None

        if with_id:
            rows.append((d["id"], d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaf"]))
            ids.append(d["id"])
        else:
            tid = add_tag_return_id(cur, d)
            ids.append(tid[0])

    stmt = "INSERT OR IGNORE INTO tags (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO tags (id, code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    cur.executemany(stmt, rows)

    return update_tags_is_leaf(cur, ids)

def add_tags_for_assignment(cur, data):
    if len(data) == 0 or not "old_tag" in data[0]:
        return cur

    for d in data:
        if not "is_leaf" in d or d["is_leaf"] is None:
            d["is_leaf"] = 1
        if not "parent" in d:
            d["parent"] = None

        tagNew = add_tag_return_tag(cur, d)
        tagOld = cur.execute("SELECT id from tags WHERE id = ?;", (d["old_tag"],)).fetchone()

        if tagNew and tagOld:
            assigId = cur.execute("SELECT id from tag_assignments WHERE old_tag = ?;", (tagOld[0],)).fetchone()
            if assigId:
                update_tag_assignments(cur, [{
                    "new_tag": tagNew[0]["id"],
                    "description": tagNew[0]["description"],
                    "id": assigId[0]
                }])

    return cur

def update_tags_is_leaf(cur, ids):
    if len(ids) == 0:
        return cur

    rows = []
    for id in ids:

        has_children = cur.execute("SELECT EXISTS(SELECT 1 FROM tags WHERE parent = ?);", (id,)).fetchone()[0]
        rows.append((0 if has_children else 1, id))

        my_parent = cur.execute("SELECT parent FROM tags WHERE id = ?;", (id,)).fetchone()[0]
        if my_parent is not None:
            rows.append((0, my_parent))

    # update is_leaf for all tags that where changed
    return cur.executemany("UPDATE tags SET is_leaf = ? WHERE id = ?;", rows)

def update_tags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        if "parent" not in d:
            d["parent"] = None
        if d["parent"] is not None and d["parent"] < 0:
            d["parent"] = None

        rows.append((d["name"], d["description"], d["parent"], d["is_leaf"], d["id"]))

    cur.executemany("UPDATE tags SET name = ?, description = ?, parent = ?, is_leaf = ? WHERE id = ?;", rows)
    # update is_leaf for all tags that where changed
    return update_tags_is_leaf(cur, [d["id"] for d in data])

def split_tags(cur, data):
    if len(data) == 0:
        return cur

    for d in data:
        if "names" not in d:
            continue

        tag = cur.execute("SELECT * FROM tags WHERE id = ?;", (d["id"],)).fetchone()
        assigsOLD = cur.execute("SELECT * FROM tag_assignments WHERE old_code = ? AND old_tag = ?", (tag["code_id"], d["id"])).fetchall()
        assigsNEW = cur.execute("SELECT * FROM tag_assignments WHERE new_code = ? AND new_tag = ?", (tag["code_id"], d["id"])).fetchall()

        children = cur.execute("SELECT * FROM tags WHERE parent = ?;", (d["id"],)).fetchall()
        first = None

        for n in d["names"]:
            # create and save new tag
            new_tag = add_tag_return_id(cur, {
                "name": n,
                "description": f"split from tag {tag['name']} with description:\n{tag['description']}",
                "code_id": tag["code_id"],
                "created": d["created"],
                "created_by": d["created_by"],
                "parent": tag["parent"],
                "is_leaf": tag["is_leaf"],
            })

            if first is None:
                first = new_tag

            rows = []
            # update tag assignments
            for a in assigsOLD:
                c = dict(a)
                c["old_tag"] = new_tag["id"]
                del c["id"]
                rows.append(c)
            for a in assigsNEW:
                c = dict(a)
                c["new_tag"] = new_tag["id"]
                del c["id"]
                rows.append(c)

            add_tag_assignments(cur, rows)

            rows = []
            dts = get_datatags_by_tag(cur, d["id"])
            for dt in dts:
                c = dict(dt)
                c["tag_id"] = new_tag["id"]
                del c["id"]
                rows.append(c)

            # create new datatags
            add_datatags(cur, rows)

        if first is not None:
            rows = []
            # update tag assignments
            for t in children:
                c = dict(t)
                c["parent"] = first["id"]
                rows.append(c)

            update_tags(cur, rows)

        # delete tag that is being split
        delete_tags(cur, [d["id"]])

    return cur

def merge_tags(cur, data):
    if len(data) == 0:
        return cur

    for d in data:
        if "ids" not in d:
            continue

        tags = cur.execute(f"SELECT * FROM tags WHERE id IN ({make_space(len(d['ids']))});", d["ids"]).fetchall()
        first = tags[0]

        if "description" not in d or len(d["description"]) == 0:
            d["description"] = f"merge tags:\n{', '.join([t['name'] for t in tags])}"

        obj = {
            "name": d["name"],
            "description": d["description"],
            "code_id": d["code_id"],
            "created": d["created"],
            "created_by": d["created_by"],
            "parent": first["parent"],
            "is_leaf": 1 if all([t["is_leaf"] == 1 for t in tags]) else 0
        }
        new_tag = add_tag_return_tag(cur, obj)

        for t in tags:

            assigsOLD = cur.execute("SELECT * FROM tag_assignments WHERE old_code = ? AND old_tag = ?;", (t["code_id"], t["id"])).fetchall()
            assigsNEW = cur.execute("SELECT * FROM tag_assignments WHERE new_code = ? AND new_tag = ?;", (t["code_id"], t["id"])).fetchall()

            rows = []
            # update tag assignments
            for a in assigsOLD:
                c = dict(a)
                c["old_tag"] = new_tag["id"]
                del c["id"]
                rows.append(c)
            for a in assigsNEW:
                c = dict(a)
                c["new_tag"] = new_tag["id"]
                del c["id"]
                rows.append(c)

            add_tag_assignments(cur, rows)

        rows = []
        children = cur.execute(f"SELECT * FROM tags WHERE parent IN ({make_space(len(tags))});", d["ids"]).fetchall()
        for t in children:
            c = dict(t)
            c["parent"] = new_tag["id"]
            rows.append(c)

        # update child tags
        update_tags(cur, rows)

        rows = []
        dts = cur.execute(f"SELECT * FROM datatags WHERE tag_id IN ({make_space(len(tags))});", d["ids"]).fetchall()
        for dt in dts:
            c = dict(dt)
            c["tag_id"] = new_tag["id"]
            del c["id"]
            rows.append(c)

        # create new datatags
        add_datatags(cur, rows)

        # delete tag that is being split
        delete_tags(cur, d["ids"])

    return cur

def delete_tags(cur, ids):
    if len(ids) == 0:
        return cur

    for id in ids:
        my_parent = cur.execute("SELECT parent FROM tags WHERE id = ?;", (id,)).fetchone()
        children = cur.execute("SELECT id FROM tags WHERE parent = ?;", (id,)).fetchall()
        # remove this node as parent
        cur.executemany("UPDATE tags SET parent = ? WHERE id = ?;", [(my_parent[0], t[0]) for t in children])

    return cur.executemany("DELETE FROM tags WHERE id = ?;",[(id,) for id in ids])

def get_datatags_by_dataset(cur, dataset):
    return cur.execute("SELECT datatags.* FROM datatags LEFT JOIN codes ON datatags.code_id = codes.id WHERE codes.dataset_id = ?;", (dataset,)).fetchall()

def get_datatags_by_code(cur, code):
    return cur.execute("SELECT * from datatags WHERE code_id = ?;", (code,)).fetchall()

def get_datatags_by_tag(cur, tag):
    return cur.execute("SELECT * from datatags WHERE tag_id = ?;", (tag,)).fetchall()

def get_datatags_by_game(cur, game):
    return cur.execute("SELECT * from datatags WHERE game_id = ?;", (game,)).fetchall()

def add_datatags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], d["game_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"]))
        else:
            rows.append((d["game_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"]))

    stmt = "INSERT OR IGNORE INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ? , ?, ?, ?);" if not with_id else "INSERT INTO datatags (id, game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_game_datatags(cur, data):
    code_id = data["code_id"]
    user_id = data["user_id"]
    game_id = data["game_id"]
    created = data["created"]

    # remove datatags not in the list
    tokeep = [int(d["tag_id"]) for d in data["tags"] if "tag_id" in d]
    results = cur.execute("SELECT id FROM datatags WHERE game_id = ? AND code_id = ? AND created_by = ?;", (game_id, code_id, user_id))
    existing = [d[0] for d in results.fetchall()]
    toremove = np.setdiff1d(np.array(existing), np.array(tokeep)).tolist()

    if len(toremove) > 0:
        stmt = f"DELETE FROM datatags WHERE created_by = ? AND id IN ({make_space(len(toremove))});"
        cur.execute(stmt, [user_id] + toremove)

    # add datatags where tags already exist in the database
    toadd = np.setdiff1d(np.array(tokeep), np.array(existing)).tolist()

    if len(toadd) > 0:
        stmt = "INSERT INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
        cur.executemany(stmt, [(game_id, int(d), code_id, created, user_id) for d in toadd])

    # add tags that do not exist in the database
    newtags = [d["tag_name"] for d in data["tags"] if "tag_name" in d]
    newtags_desc = [d["description"] for d in data["tags"] if "tag_name" in d]

    if len(newtags) > 0:
        stmt = "INSERT INTO tags (name, description, code_id, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?);"
        rows = []
        for i, d in enumerate(newtags):
            rows.append((d, newtags_desc[i], code_id, created, user_id, None, 1))
        # collect new tag ids
        cur.executemany(stmt, rows)

        result = cur.execute(f"SELECT id FROM tags WHERE created_by = ? AND name IN ({make_space(len(newtags))});", [user_id] + newtags)
        new_tag_ids = [d[0] for d in result]

        # add datatags for new these tags
        if len(new_tag_ids) > 0:
            stmt = "INSERT INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
            cur.executemany(stmt, [(game_id, d, code_id, created, user_id) for d in new_tag_ids])

    return cur

def delete_datatags(cur, data):
    return cur.executemany("DELETE FROM datatags WHERE id = ?;", [(id,) for id in data])

def get_evidence_by_dataset(cur, dataset):
    return cur.execute(
        "SELECT evidence.* from evidence LEFT JOIN games ON evidence.game_id = games.id WHERE games.dataset_id = ?;",
        (dataset,)
    ).fetchall()
def get_evidence_by_code(cur, code):
    return cur.execute("SELECT * from evidence WHERE code_id = ?;", (code,)).fetchall()
def get_evidence_by_tag(cur, tag):
    return cur.execute("SELECT * from evidence WHERE tag_id = ?;", (tag,)).fetchall()

def add_evidence(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:

        if "filepath" not in d:
            d["filepath"] = None
        if "tag_id" not in d:
            d["tag_id"] = None

        if with_id:
            rows.append((d["id"], d["game_id"], d["code_id"], d["tag_id"], d["filepath"], d["description"], d["created"], d["created_by"]))
        else:
            rows.append((d["game_id"], d["code_id"], d["tag_id"], d["filepath"], d["description"], d["created"], d["created_by"]))

    stmt = "INSERT INTO evidence (game_id, code_id, tag_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO evidence (id, game_id, code_id, tag_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_evidence(cur, data, base_path):
    if len(data) == 0:
        return

    rows = []
    for r in data:
        if "filepath" not in r:
            r["filepath"] = None
        if "tag_id" not in r:
            r["tag_id"] = None

        rows.append((r["description"], r["filepath"], r["tag_id"], r["id"]))

    return cur.executemany("UPDATE evidence SET description = ?, filepath = ?, tag_id = ? WHERE id = ?;", rows)

def delete_evidence(cur, data, base_path, backup_path):
    filenames = cur.execute(f"SELECT filepath FROM evidence WHERE id IN ({make_space(len(data))});", data).fetchall()
    cur.executemany("DELETE FROM evidence WHERE id = ?;", [(id,) for id in data])

    for f in filenames:
        if f[0] is not None:
            base_path.joinpath(f[0]).unlink(missing_ok=True)
            backup_path.joinpath(f[0]).unlink(missing_ok=True)

def get_memos_by_dataset(cur, dataset):
    return cur.execute("SELECT memos.* FROM memos LEFT JOIN users ON memos.created_by = users.id WHERE users.dataset_id = ?;", (dataset,)).fetchall()
def get_memos_by_code(cur, code):
    return cur.execute("SELECT * FROM memos WHERE code_id = ?;", (code,)).fetchall()
def get_memos_by_game(cur, game):
    return cur.execute("SELECT * FROM memos WHERE game_id = ?;", (game,)).fetchall()
def get_memos_by_tag(cur, tag):
    return cur.execute("SELECT * FROM memos WHERE tag_id = ?;", (tag,)).fetchall()

def add_memos(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        stmt = "INSERT INTO memos ("
        with_id = "id" in d
        with_tag = "tag_id" in d

        t = ()
        if with_id:
            t = t + (d["id"],)
            stmt = stmt + "id, "

        t = t + (d["game_id"], d["code_id"], d["description"], d["created"], d["created_by"])
        stmt = stmt + "game_id, code_id, description, created, created_by"
        if with_tag:
            t = t + (d["tag_id"],)
            stmt = stmt + ", tag_id"

        stmt = stmt + f") VALUES ({make_space(len(t))});"
        cur.execute(stmt, t)

    return cur.executemany(stmt, rows)

def get_tag_assignments_by_dataset(cur, dataset):
    return cur.execute("SELECT tag_assignments.* from tag_assignments LEFT JOIN codes ON tag_assignments.old_code = codes.id WHERE codes.dataset_id = ?;", (dataset,)).fetchall()
def get_tag_assignments_by_old_code(cur, code):
    return cur.execute("SELECT * from tag_assignments WHERE old_code = ?;", (code,)).fetchall()
def get_tag_assignments_by_new_code(cur, code):
    return cur.execute("SELECT * from tag_assignments WHERE new_code = ?;", (code,)).fetchall()
def get_tag_assignments_by_codes(cur, old_code, new_code):
    return cur.execute("SELECT * from tag_assignments WHERE old_code = ? AND new_code = ?;", (old_code, new_code)).fetchall()

def add_tag_assignments(cur, data):
    if len(data) == 0:
        return cur
    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], d["old_code"], d["new_code"], d["old_tag"], d["new_tag"], d["description"], d["created"]))
        else:
            rows.append((d["old_code"], d["new_code"], d["old_tag"], d["new_tag"], d["description"], d["created"]))

    stmt = "INSERT OR IGNORE INTO tag_assignments (old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def add_tag_assignments_for_codes(cur, old_code, new_code, data):
    if len(data) == 0:
        return cur
    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], old_code, new_code, d["old_tag"], d["new_tag"], d["description"], d["created"]))
        else:
            rows.append((old_code, new_code, d["old_tag"], d["new_tag"], d["description"], d["created"]))

    stmt = "INSERT INTO tag_assignments (old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_tag_assignments(cur, data):
    if len(data) == 0:
        return cur
    rows = []
    for d in data:
        rows.append((d["new_tag"], d["description"], d["id"], d["old_code"], d["new_code"]))
    return cur.executemany("UPDATE tag_assignments SET new_tag = ?, description = ? WHERE id = ? AND old_code = ? AND new_code = ?;", rows)

def delete_tag_assignments(cur, data):
    return cur.executemany("DELETE FROM tag_assignments WHERE id = ?;", [(id,) for id in data])


def get_code_transitions_by_dataset(cur, dataset):
    return cur.execute(
        "SELECT code_transitions.* from code_transitions LEFT JOIN codes ON code_transitions.old_code = codes.id WHERE codes.dataset_id = ?;",
        (dataset,)
    ).fetchall()
def get_code_transitions_by_old_code(cur, code):
    return cur.execute("SELECT * from code_transitions WHERE old_code = ?;", (code,)).fetchall()
def get_code_transitions_by_new_code(cur, code):
    return cur.execute("SELECT * from code_transitions WHERE new_code = ?;", (code,)).fetchall()
def get_code_transitions_by_codes(cur, old_code, new_code):
    return cur.execute("SELECT * from code_transitions WHERE old_code = ? AND new_code = ?;", (old_code, new_code)).fetchall()

def add_code_transitions(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if "finished" not in d:
            d["finished"] = None

        if with_id:
            rows.append((d["id"], d["old_code"], d["new_code"], d["started"], d["finished"]))
        else:
            rows.append((d["old_code"], d["new_code"], d["started"], d["finished"]))

    stmt = "INSERT INTO code_transitions (old_code, new_code, started, finished) VALUES (?, ?, ?, ?);" if not with_id else "INSERT INTO code_transitions (id, old_code, new_code, started, finished) VALUES (?, ?, ?, ?, ?);"

    return cur.executemany(stmt, rows)

def update_code_transitions(cur, data):
    if len(data) == 0:
        return cur

    return cur.executemany("UPDATE code_transitions SET finished = ? WHERE id = ?;", [(d["finished"], d["id"]) for d in data])

def delete_code_transitions(cur, data):
    return cur.executemany("DELETE FROM code_transitions WHERE id = ?;", [(id,) for id in data])

def prepare_transition(cur, old_code, new_code):

    old_tags = get_tags_by_code(cur, old_code)
    assigned = {}

    rows = []
    print("preparing transition")
    # create/copy tags from old code that do not have a parent
    for t in old_tags:

        # check if a tag assignment alraady exists
        cur.execute("SELECT id FROM tag_assignments WHERE old_code = ? AND new_code = ? AND old_tag = ?;", (old_code, new_code, t["id"]))
        tag_assigned_id = cur.fetchone()

        # if the old tag already has an assignment we dont need to create a new tag
        if tag_assigned_id is not None:
            assigned[t["id"]] = tag_assigned_id
            print("\t", "tag", t["name"], "is already assigned")
            continue

        # no assignemnt - but check if new tag with same name already exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM tags WHERE code_id = ? AND name = ?);", (new_code, t["name"]))
        exists = cur.fetchone()[0]

        if not exists:
            new_tag = add_tag_return_tag(cur, {
                "code_id": new_code,
                "name": t["name"],
                "description": t["description"],
                "created": t["created"],
                "created_by": t["created_by"],
                "parent": None,
                "is_leaf": t["is_leaf"]
            })
            print(new_tag)
            assigned[t["id"]] = new_tag["id"]

    new_tags = get_tags_by_code(cur, new_code)

    for t in old_tags:

        has_assigned = assigned[t["id"]] if t["id"] in assigned else None

        # find matching new tag
        tNew = [tag for tag in new_tags if has_assigned is not None and tag["id"] == has_assigned or tag["name"] == t["name"]]

        if len(tNew) == 0:
            print("ERROR")
            print("missing tag", t["name"])
            raise Exception("missing tag " + t["name"])

        # check if tag assignment already exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM tag_assignments WHERE old_code = ? AND new_code = ? AND old_tag = ?);", (old_code, new_code, t["id"]))
        exists = cur.fetchone()[0]

        if not exists:
            add_tag_assignments(cur, [{
                "old_code": old_code,
                "new_code": new_code,
                "old_tag": t["id"],
                "new_tag": tNew[0]["id"],
                "created": tNew[0]["created"],
                "description": "INITIAL COPY"
            }])

        rows = []

        # get datatags in old code
        datatags = get_datatags_by_tag(cur, t["id"])
        for d in datatags:

            # check if datatag already exists
            cur.execute("SELECT EXISTS(SELECT 1 FROM datatags WHERE code_id = ? AND game_id = ? AND tag_id = ? AND created_by = ?);", (new_code, d["game_id"], tNew[0]["id"], d["created_by"]))
            exists = cur.fetchone()[0]

            if not exists:
                rows.append({
                    "game_id": d["game_id"],
                    "tag_id": tNew[0]["id"],
                    "code_id": new_code,
                    "created": d["created"],
                    "created_by": d["created_by"],
                })

        # add datatags to new code
        add_datatags(cur, rows)

        if t["parent"] is not None:
            pTag = [tag for tag in old_tags if tag["id"] == t["parent"]]

            has_assigned_p = assigned[pTag["id"]] if pTag["id"] in assigned else None

            # find matching new parent tag
            tNewParent = [tag for tag in new_tags if has_assigned_p is not None and tag["id"] == has_assigned_p or tag["name"] == pTag["name"]]

            if len(tNewParent) == 0:
                print("ERROR")
                print("missing tag parent", pTag["name"])
                raise Exception("missing tag parent " + pTag["name"])

            update_tags(cur, [{
                "name": tNew[0]["name"],
                "description": tNew[0]["description"],
                "parent": tNewParent[0]["id"],
                "is_leaf": tNew[0]["is_leaf"],
                "id": tNew[0]["id"]
            }])

    # get evidence for old code
    ev = get_evidence_by_code(cur, old_code)

    rows = []
    for d in ev:
        # check if evidence already exists
        cur.execute("SELECT EXISTS(SELECT 1 FROM evidence WHERE game_id = ? AND description = ? AND created_by = ? AND code_id = ?);", (d["game_id"], d["description"], d["created_by"], new_code))
        exists = cur.fetchone()[0]

        if not exists:
            rows.append({
                "game_id": d["game_id"],
                "code_id": new_code,
                "filepath": d["filepath"],
                "description": d["description"],
                "created": d["created"],
                "created_by": d["created_by"],
            })

    # add evidence for old code
    add_evidence(cur, rows)

    return cur

def check_transition(cur, old_code, new_code):

    ds = cur.execute("SELECT dataset_id FROM codes WHERE id = ?;", (old_code,)).fetchone()[0]
    games = get_games_by_dataset(cur, ds)

    tags_need_update = []

    now = datetime.now(timezone.utc).timestamp()
    for g in games:
        dts_old = cur.execute("SELECT * FROM datatags WHERE game_id = ? AND code_id = ?;", (g["id"], old_code)).fetchall();
        dts_new = cur.execute("SELECT * FROM datatags WHERE game_id = ? AND code_id = ?;", (g["id"], new_code)).fetchall();

        if len(dts_old) > 0 and len(dts_new) == 0:
            rows = []
            for d in dts_old:
                obj = dict(d)

                tag_assig = cur.execute("SELECT * FROM tag_assignments WHERE old_tag = ? AND old_code = ? AND new_code = ?;", (obj["tag_id"], old_code, new_code)).fetchone()
                if not tag_assig:
                    tag_old = cur.execute("SELECT * FROM tags WHERE id = ? AND code_id = ?;", (obj["tag_id"], old_code)).fetchone();
                    # create tag and assignment
                    tag_new_id = add_tag_return_tag(cur, {
                        "name": tag_old["name"],
                        "description": tag_old["description"],
                        "code_id": new_code,
                        "parent": None,
                        "is_leaf": tag_old["is_leaf"],
                        "created": tag_old["created"],
                        "created_by": tag_old["created_by"],
                    })
                    add_tag_assignments(cur, [{
                        "old_code": old_code,
                        "new_code": new_code,
                        "old_tag": tag_old["id"],
                        "new_tag": tag_new_id,
                        "description": "",
                        "created": now
                    }])
                    tags_need_update.append((tag_old["id"], tag_new_id))
                else:
                    tag_new_id = tag_assig["new_tag"]

                del obj["id"]
                obj["tag_id"] = tag_new_id,
                obj["code_id"] = new_code,
                rows.append(d)

            add_datatags(cur, rows)

        # TODO: do the same for evidence

    # update parent field for newly created tags
    for (old_tag, new_tag) in tags_need_update:

        tag_old = cur.execute("SELECT * FROM tags WHERE id = ?;", (old_tag,)).fetchone()
        # get parent for old tag
        p_old = tag_old["parent"]
        if p_old:
            # get assignment for old tag's parent
            assign = cur.execute("SELECT * FROM tag_assignments WHERE old_tag = ? AND old_code = ? AND new_code = ?;", (p_old, old_code, new_code)).fetchone()
            # find matching parent for new tag
            tag_new = cur.execute("SELECT * FROM tags WHERE id = ?;", (new_tag,)).fetchone()
            obj = dict(tag_new)
            obj["parent"] = assign["new_tag"]
            # update new tag
            update_tags(cur, [obj])

    return cur
