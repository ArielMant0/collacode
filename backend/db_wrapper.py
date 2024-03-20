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

def add_tags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], d["code_id"], d["name"], d["description"], d["created"], d["created_by"]))
        else:
            rows.append((d["code_id"], d["name"], d["description"], d["created"], d["created_by"]))

    stmt = "INSERT OR IGNORE INTO tags (code_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO tags (id, code_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

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
    return cur.execute("SELECT * FROM memos LEFT JOIN codes ON memos.code_id = codes.id WHERE codes.dataset_id = ?;", (dataset,))
def get_memos_by_code(cur, code):
    return cur.execute("SELECT * FROM memos WHERE code_id = ?;", (code,))
def get_memos_by_game(cur, game):
    return cur.execute("SELECT * FROM memos WHERE game_id = ?;", (game,))
def get_memos_by_tag(cur, tag):
    return cur.execute("SELECT * FROM memos WHERE tag_id = ?;", (tag,))

def add_memos(cur, data):
    rows = []
    for d in data:
        stmt = "INSERT OR IGNORE INTO tag_groups ("
        with_id = "id" in d
        with_tag = "tag_id" in d

        t = ()
        if with_id:
            t = t + (d["id"],)
            stmt = stmt + "id, "

        t = t + (d["dataset_id"], d["old_code"], d["new_code"], d["description"], d["created"])
        stmt = stmt + "dataset_id, old_code, new_code, description, created"
        if with_tag:
            t = t + (d["tag_id"],)
            stmt = stmt + "tag_id"

        stmt = stmt + f") VALUES ({make_space(len(t))});"
        cur.execute(stmt, t)

    return cur.executemany(stmt, rows)

def get_tag_groups_by_dataset(cur, dataset):
    return cur.execute("SELECT * FROM tag_groups WHERE dataset_id = ?;", (dataset,))
def get_tag_groups_by_old_code(cur, code):
    return cur.execute("SELECT * from tag_groups WHERE old_code = ?;", (code,))
def get_tag_groups_by_new_code(cur, code):
    return cur.execute("SELECT * from tag_groups WHERE new_code = ?;", (code,))
def get_tag_groups_by_codes(cur, old_code, new_code):
    return cur.execute("SELECT * from tag_groups WHERE old_code = ? AND new_code = ?;", (old_code, new_code))

def add_tag_groups(cur, dataset, old_code, new_code, data):
    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], dataset, old_code, new_code, d["name"], d["description"], d["created"]))
        else:
            rows.append((dataset, old_code, new_code, d["name"], d["description"], d["created"]))

    stmt = "INSERT OR IGNORE INTO tag_groups (dataset_id, old_code, new_code, name, description, created) VALUES (?, ?, ?, ?, ?, ?);" if not with_id else "INSERT OR IGNORE INTO tag_groups (id, dataset_id, old_code, new_code, name, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);"
    return cur.executemany(stmt, rows)

def delete_tag_groups(cur, data):
    return cur.executemany("DELETE FROM tag_groups WHERE id = ?;", [(id,) for id in data])

def get_code_transitions_by_dataset(cur, dataset):
    return cur.execute("""SELECT * FROM code_transitions LEFT JOIN tag_groups
        ON code_transitions.group_id = tag_groups.id WHERE tag_groups.dataset_id = ?;""",
        (dataset,)
    )
def get_code_transitions_by_old_code(cur, code):
    return cur.execute("""SELECT * FROM code_transitions LEFT JOIN tag_groups
        ON code_transitions.group_id = tag_groups.id WHERE tag_groups.old_code = ?;""",
        (code,)
    )
def get_code_transitions_by_new_code(cur, code):
    return cur.execute("""SELECT * FROM code_transitions LEFT JOIN tag_groups
        ON code_transitions.group_id = tag_groups.id WHERE tag_groups.new_code = ?;""",
        (code,)
    )

def add_code_transitions(cur, group, data):
    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append((d["id"], d["tag_id"], group))
        else:
            rows.append((d["tag_id"], group))

    stmt = "INSERT OR IGNORE INTO code_transitions (tag_id, group_id) VALUES (?, ?);" if not with_id else "INSERT OR IGNORE INTO code_transitions (id,tag_id, group_id) VALUES (?, ?, ?);"
    return cur.executemany(stmt, rows)

def delete_code_transitions(cur, data):
    return cur.executemany("DELETE FROM code_transitions WHERE id = ?;", [(id,) for id in data])
