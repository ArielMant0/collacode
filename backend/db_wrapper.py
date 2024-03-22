import numpy as np

def make_space(length):
    return ",".join(["?"] * length)

def get_datasets(cur):
    return cur.execute("SELECT * from datasets").fetchall()

def add_dataset(cur, name, description):
    return cur.execute("INSERT OR IGNORE INTO datasets (name, description) VALUES (?, ?);", (name, description))

def get_games_by_dataset(cur, dataset):
    return cur.execute("SELECT * from games WHERE dataset_id = ?;", (dataset,)).fetchall()

def add_games(cur, dataset, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], dataset, d["name"], d["year"], d["played"], d["url"]))
        else:
            rows.append((dataset, d["name"], d["year"], d["played"], d["url"]))

    stmt = "INSERT OR IGNORE INTO games (dataset_id, name, year, played, url) VALUES (?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO games (id, dataset_id, name, year, played, url) VALUES (?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_games(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        rows.append((d["name"], d["year"], d["played"], d["url"], d["id"]))
    return cur.executemany("UPDATE games SET name = ?, year = ?, played = ?, url = ? WHERE id = ?;", rows)

def delete_games(cur, data):
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

    stmt = "INSERT OR IGNORE INTO users (dataset_id, name, role, email) VALUES (?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO users (id, dataset_id, name, role, email) VALUES (?, ?, ?, ?, ?);"
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

    stmt = "INSERT OR IGNORE INTO codes (dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO codes (id, dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
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
        "SELECT * from tags LEFT JOIN codes ON tags.code_id = codes.id WHERE codes.dataset_id = ?;",
        (dataset,)
    ).fetchall()
def get_tags_by_code(cur, code):
    return cur.execute("SELECT * from tags WHERE code_id = ?;", (code,)).fetchall()

def add_tag_return_id(cur, d):
    cur = cur.execute(
        "INSERT OR IGNORE INTO tags (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id;",
        (d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaft"])
    )
    return next(cur)

def add_tags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]

    for d in data:
        if not "is_leaf" in d or d["is_leaf"] is None:
            d["is_leaf"] = 1
        if not "parent" in d:
            d["parent"] = None

        if with_id:
            rows.append((d["id"], d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaf"]))
        else:
            rows.append((d["code_id"], d["name"], d["description"], d["created"], d["created_by"], d["parent"], d["is_leaf"]))

    stmt = "INSERT INTO tags (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?);" if not with_id else "INSERT INTO tags (id, code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_tags(cur, data):
    if len(data) == 0:
        return cur
    rows = []
    for d in data:
        rows.append((d["name"], d["description"], d["parent"], d["is_leaf"], d["id"]))
    return cur.executemany("UPDATE tags SET name = ?, description = ?, parent = ?, is_leaf = ?, WHERE id = ?;", rows)

def delete_tags(cur, ids):
    return cur.executemany("DELETE FROM tags WHERE id = ?;", [(id,) for id in ids])

def get_datatags_by_code(cur, code):
    return cur.execute("SELECT * from datatags WHERE code_id = ?;", (code,)).fetchall()

def get_datatags_by_tag(cur, tag):
    return cur.execute("SELECT * from datatags WHERE tag_id = ?;", (tag,)).fetchall()

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

    stmt = "INSERT OR IGNORE INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ? , ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO datatags (id, game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
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
        stmt = "INSERT INTO tags (name, description, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
        rows = []
        for i, d in enumerate(newtags):
            rows.append((d, newtags_desc[i], code_id, created, user_id))
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
        "SELECT * from image_evidence LEFT JOIN games ON image_evidence.game_id = games.id WHERE games.dataset_id = ?;",
        (dataset,)
    ).fetchall()
def get_evidence_by_code(cur, code):
    return cur.execute("SELECT * from image_evidence WHERE code_id = ?;", (code,)).fetchall()

def add_evidence(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], d["game_id"], d["code_id"], d["filepath"], d["description"], d["created"], d["created_by"]))
        else:
            rows.append((d["game_id"], d["code_id"], d["filepath"], d["description"], d["created"], d["created_by"]))

    stmt = "INSERT OR IGNORE INTO image_evidence (game_id, code_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO image_evidence (id, game_id, code_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_evidence(cur, data):
    rows = []
    for r in data:
        data.append((r["description"], r["id"]))
    return cur.executemany("UPDATE image_evidence SET description = ? WHERE id = ?;", rows)

def delete_evidence(cur, data, base_path):
    filenames = cur.execute(f"SELECT filepath FROM image_evidence WHERE id IN ({make_space(len(data))});", data).fetchall()
    cur.executemany("DELETE FROM image_evidence WHERE id = ?;", [(id,) for id in data])

    for f in filenames:
        base_path.joinpath(f[0]).unlink(missing_ok=True)

def get_memos_by_dataset(cur, dataset):
    return cur.execute("SELECT * FROM memos LEFT JOIN codes ON memos.code_id = codes.id WHERE codes.dataset_id = ?;", (dataset,)).fetchall()
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
        stmt = "INSERT OR IGNORE INTO memos ("
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

    stmt = "INSERT OR IGNORE INTO tag_assignments (old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);"
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

    stmt = "INSERT OR IGNORE INTO tag_assignments (old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def update_tag_assignments(cur, data):
    if len(data) == 0:
        return cur
    rows = []
    for d in data:
        rows.append((d["new_tag"], d["description"], d["id"]))
    return cur.executemany("UPDATE tag_assignments SET new_tag = ?, description = ? WHERE id = ?;", rows)

def delete_tag_assignments(cur, data):
    return cur.executemany("DELETE FROM tag_assignments WHERE id = ?;", [(id,) for id in data])


def get_code_transitions_by_dataset(cur, dataset):
    return cur.execute(
        "SELECT * from code_transitions LEFT JOIN codes ON code_transitions.old_code = codes.id WHERE codes.dataset_id = ?;",
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
        if with_id:
            rows.append((d["id"], d["old_code"], d["new_code"], d["created"], d["created_by"]))
        else:
            rows.append((d["old_code"], d["new_code"], d["created"], d["created_by"]))

    stmt = "INSERT OR IGNORE INTO code_transitions (old_code, new_code, created, created_by) VALUES (?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO code_transitions (id, old_code, new_code, created, created_by) VALUES (?, ?, ?, ?, ?);"

    return cur.executemany(stmt, rows)

def delete_code_transitions(cur, data):
    return cur.executemany("DELETE FROM code_transitions WHERE id = ?;", [(id,) for id in data])

def copy_tags_for_transition(cur, old_code, new_code):

    old_tags = get_tags_by_code(cur, old_code)

    rows = []
    # create/copy tags from old code that do not have a parent
    for t in old_tags:
        rows.append({
            "code_id": new_code,
            "name": t["name"],
            "description": t["description"],
            "created": t["created"],
            "created_by": t["created_by"],
            "parent": None,
            "is_leaf": t["is_leaf"]
        })

    add_tags(cur, rows)

    new_tags = get_tags_by_code(cur, new_code)

    rows = []

    for t in old_tags:
        # find matching new tag
        tNew = [tag for tag in new_tags if tag["name"] == t["name"]]

        if len(tNew) == 0:
            print("ERROR")
            print("missing tag", t["name"])
            raise "asdsa"

        add_tag_assignments(cur, [{
            "old_code": old_code,
            "new_code": new_code,
            "old_tag": t["id"],
            "new_tag": tNew[0]["id"],
            "created": tNew[0]["created"],
            "description": "INITIAL COPY"
        }])

        if t["parent"] is not None:
            pTag = [tag for tag in old_tags if tag["id"] == t["parent"]]
            # find matching new parent tag
            tNewParent = [tag for tag in new_tags if tag["name"] == pTag["name"]]

            if len(tNewParent) == 0:
                print("ERROR")
                print("missing tag parent", t["name"])
                raise "asdsa"

            update_tags(cur, [{
                "name": tNew["name"],
                "description": tNew["description"],
                "parent": tNewParent["id"],
                "is_leaf": tNew["is_leaf"]
            }])

    return cur
