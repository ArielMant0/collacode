import json
from collections import namedtuple
from datetime import datetime, timezone
from argon2 import PasswordHasher

import numpy as np
from table_constants import (
    TBL_CODES,
    TBL_DATASETS,
    TBL_DATATAGS,
    TBL_EVIDENCE,
    TBL_EXPERTISE,
    TBL_ITEMS,
    TBL_LOGS,
    TBL_META_AG,
    TBL_META_CATS,
    TBL_META_CON_CAT,
    TBL_META_CON_EV,
    TBL_META_CON_TAG,
    TBL_META_GROUPS,
    TBL_META_ITEMS,
    TBL_PRJ_USERS,
    TBL_TAG_ASS,
    TBL_TAGS,
    TBL_TRANS,
    TBL_UPDATES,
    TBL_USERS,
)


def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

def one_or_none(cur, stmt, data):
    res = cur.execute(stmt, data).fetchone()
    return res[0] if res is not None else None

def log_update(cur, name, dataset):
    return cur.execute(
        f"INSERT INTO {TBL_UPDATES} (name, dataset_id, timestamp) VALUES (?,?,?) ON CONFLICT (name, dataset_id) DO UPDATE SET timestamp = EXCLUDED.timestamp;",
        (name, dataset, get_millis()),
    )


def log_action(cur, action, data=None, user=None):
    return cur.execute(
        f"INSERT INTO {TBL_LOGS} (user_id, timestamp, action, data) VALUES (?,?,?,?)",
        (user, get_millis(), action, json.dumps(data) if data is not None else None),
    )


def make_space(length):
    return ",".join(["?"] * length)


def get_meta_table(cur, dataset):
    res = cur.execute(
        f"SELECT meta_table FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)
    ).fetchone()
    if res is None:
        return None

    return res["meta_table"] if isinstance(res, dict) else res[0]

def get_last_updates(cur, dataset):
    return cur.execute(f"SELECT * FROM {TBL_UPDATES} WHERE dataset_id = ?;", (dataset,)).fetchall()


def getColumnType(str):
    str = str.lower()
    if str == "integer" or str == "date":
        return "INTEGER"
    if str == "float":
        return "REAL"
    return "TEXT"


def get_dataset_schema(cur, dataset):
    s = cur.execute(f"SELECT schema FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)).fetchone()
    if s is not None:
        it = s["schema"] if isinstance(s, dict) else s[0]
        return json.loads(it if isinstance(it, str) else it.decode("utf-8"))
    return None


def get_dataset_by_code(cur, code):
    ds = cur.execute(
        f"SELECT d.* FROM {TBL_DATASETS} d LEFT JOIN {TBL_CODES} c ON c.dataset_id = d.id WHERE c.id = ?;",
        (code,),
    ).fetchone()
    if ds is None:
        return None

    del ds["meta_table"]
    ds["schema"] = json.loads(ds["schema"] if isinstance(ds["schema"], str) else ds["schema"].decode("utf-8"))
    return ds


def get_dataset_id_by_code(cur, code):
    ds = cur.execute(
        f"SELECT d.id FROM {TBL_DATASETS} d LEFT JOIN {TBL_CODES} c ON c.dataset_id = d.id WHERE c.id = ?;",
        (code,),
    ).fetchone()

    return ds[0] if ds is not None else None

def get_datasets(cur):
    datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS}").fetchall()
    for ds in datasets:
        del ds["meta_table"]
        ds["schema"] = json.loads(ds["schema"] if isinstance(ds["schema"], str) else ds["schema"].decode("utf-8"))

    return datasets

def add_dataset(cur, obj):

    obj["meta_table"] = None

    if "item_name" not in obj:
        raise ValueError("missing item name")

    if "users" not in obj or len(obj["users"]) == 0:
        raise ValueError("too few users")

    if "description" not in obj:
        obj["description"] = None

    if "meta_item_name" not in obj:
        obj["meta_item_name"] = None

    res = cur.execute(
        f"INSERT INTO {TBL_DATASETS} (name, description, meta_table, " +
        "item_name, meta_item_name) VALUES (:name, :description, " +
        ":meta_table, :item_name, :meta_item_name) RETURNING id;",
        obj
    ).fetchone()

    id = res[0]

    new_users = [u for u in obj["users"] if "id" not in u]
    users_ids = [u["id"] for u in obj["users"] if "id" in u]
    for u in new_users:
        users_ids.append(add_user_return_id(cur, u))

    add_users_to_project(cur, id, users_ids)

    if "schema" in obj:
        schema = bytes(json.dumps(obj["schema"]), "utf-8")
        obj["meta_table"] = "data_" + str(id)

        stmt = f"CREATE TABLE {obj['meta_table']} (id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, "

        cols = obj["schema"]["columns"]
        for c in cols:
            # TODO: replace with sth safer
            stmt += f"{c['name']} {getColumnType(c['type'])}"

            # required column
            if c["required"]:
                stmt += " NOT NULL"
            # default value
            if "default_value" in c:
                stmt += f" DEFAULT {c['default_value']}"

            stmt += ","

        stmt += "FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE);"
        cur.execute(stmt)
        cur.execute(
            f"UPDATE {TBL_DATASETS} SET meta_table = ?, schema = ? WHERE id = ?;",
            (obj["meta_table"], schema, id)
        )

    code = {
        "name": obj["code_name"],
        "description": obj["code_desc"],
        "created": get_millis(),
        "created_by": obj["user_id"],
    }

    add_codes(cur, id, [code])

    log_update(cur, TBL_DATASETS, id)
    log_action(cur, "add dataset", obj)

    return id


def get_items_by_dataset(cur, dataset):
    tbl_name = get_meta_table(cur, dataset)
    if tbl_name is None:
        return cur.execute(f"SELECT * FROM {TBL_ITEMS} WHERE dataset_id = ? ORDER BY id;", (dataset,)).fetchall()

    schema = get_dataset_schema(cur, dataset)
    columns = ""
    for i, c in enumerate(schema["columns"]):
        columns += 'g.'+c["name"]
        if i < len(schema["columns"])-1:
            columns += ", "
        else:
            columns += " "

    return cur.execute(
        f"SELECT i.*, {columns} FROM {TBL_ITEMS} i LEFT JOIN {tbl_name} g ON i.id = g.item_id WHERE i.dataset_id = ?;",
        (dataset,),
    ).fetchall()

def get_items_merged_by_code(cur, code):

    ds = get_dataset_by_code(cur, code)
    dataset = ds["id"]

    tbl_name = get_meta_table(cur, dataset)
    if tbl_name is None:
        return cur.execute(f"SELECT * FROM {TBL_ITEMS} WHERE dataset_id = ? ORDER BY id;", (dataset,)).fetchall()

    schema = get_dataset_schema(cur, dataset)
    columns = ""
    for i, c in enumerate(schema["columns"]):
        columns += 'g.'+c["name"]
        if i < len(schema["columns"])-1:
            columns += ", "
        else:
            columns += " "

    items = cur.execute(
        f"SELECT i.*, {columns} FROM {TBL_ITEMS} i LEFT JOIN {tbl_name} g ON i.id = g.item_id WHERE i.dataset_id = ? ORDER BY i.id;",
        (dataset,)
    ).fetchall()

    for d in items:
        d["tags"] = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ?;", (d["id"], code)
        ).fetchall()

    return items

def add_item_return_id(cur, d):

    dataset = d["dataset_id"]
    tbl_name = get_meta_table(cur, dataset)
    columns = None
    columns_colon = None
    if tbl_name is not None:
        schema = get_dataset_schema(cur, dataset)
        columns = ""
        columns_colon = ""
        for i, c in enumerate(schema["columns"]):
            columns += c["name"]
            columns_colon += ":"+c["name"]
            if i < len(schema["columns"])-1:
                columns += ", "
                columns_colon += ", "
            else:
                columns += " "
                columns_colon += " "

    if "description" not in d:
        d["description"] = None
    if "url" not in d:
        d["url"] = None
    if "teaser" not in d:
        d["teaser"] = None

    res = cur.execute(
        f"INSERT INTO {TBL_ITEMS} (dataset_id, name, description, url, teaser) VALUES (?, ?, ?, ?, ?) RETURNING id;",
        (dataset, d["name"], d["description"], d["url"], d["teaser"]),
    ).fetchone()
    d["item_id"] = res[0]

    if tbl_name is not None:
        for c in schema["columns"]:
            if c["name"] not in d:
                d[c["name"]] = None

        cur.execute(
            f"INSERT INTO {tbl_name} (item_id, {columns}) VALUES (:item_id, {columns_colon});", d
        )

    log_update(cur, TBL_ITEMS, dataset)
    log_action(cur, "add items", {"names": [d["name"]]})

    return d["item_id"]

def add_items(cur, dataset, data):
    if len(data) == 0:
        return cur

    tbl_name = get_meta_table(cur, dataset)
    columns = None
    columns_colon = None
    if tbl_name is not None:
        schema = get_dataset_schema(cur, dataset)
        columns = ""
        columns_colon = ""
        for i, c in enumerate(schema["columns"]):
            columns += c["name"]
            columns_colon += ":"+c["name"]
            if i < len(schema["columns"])-1:
                columns += ", "
                columns_colon += ", "
            else:
                columns += " "
                columns_colon += " "

    for d in data:
        if "description" not in d:
            d["description"] = None
        if "url" not in d:
            d["url"] = None
        if "teaser" not in d:
            d["teaser"] = None

        if "id" in d:
            cur.execute(
                f"INSERT INTO {TBL_ITEMS} (id, dataset_id, name, description, url, teaser) VALUES (?, ?, ?, ?, ?, ?);",
                (d["id"], dataset, d["name"], d["description"], d["url"], d["teaser"]),
            )
            d["item_id"] = d["id"]
        else:
            res = cur.execute(
                f"INSERT INTO {TBL_ITEMS} (dataset_id, name, description, url, teaser) VALUES (?, ?, ?, ?, ?) RETURNING id;",
                (dataset, d["name"], d["description"], d["url"], d["teaser"]),
            ).fetchone()
            d["item_id"] = res[0]

        if tbl_name is not None:
            for c in schema["columns"]:
                if c["name"] not in d:
                    d[c["name"]] = None

            cur.execute(
                f"INSERT INTO {tbl_name} (item_id, {columns}) VALUES (:item_id, {columns_colon});",
                d,
            )

    log_update(cur, TBL_ITEMS, dataset)
    return log_action(cur, "add items", {"names": [d["name"] for d in data]})


def update_items(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    col_str = {}

    for d in data:
        ds = d["dataset_id"]
        datasets.add(ds)

        cur.execute(
            f"UPDATE {TBL_ITEMS} SET name = ?, description = ?, url = ?, teaser = ? WHERE id = ?;",
            (d["name"], d["description"], d["url"], d["teaser"], d["id"]),
        )

        tbl_name = get_meta_table(cur, ds)

        if tbl_name is not None:
            if ds not in col_str:
                schema = get_dataset_schema(cur, ds)
                columns = ""
                for i, c in enumerate(schema["columns"]):
                    columns += c["name"] + " = ?"
                    if i < len(schema["columns"])-1:
                        columns += ", "
                    else:
                        columns += " "

                col_str[ds] = columns

            vals = []
            for c in schema["columns"]:
                vals.append(d[c["name"]])

            vals.append(d["id"])

        if tbl_name is not None:
            cur.execute(f"UPDATE {tbl_name} SET {col_str[ds]} WHERE item_id = ?;", tuple(vals))

    for d in datasets:
        log_update(cur, TBL_ITEMS, d)
    return log_action(cur, "update items", {"names": [d["name"] for d in data]})


def delete_items(cur, data, base_path, backup_path):
    if len(data) == 0:
        return cur

    ds = cur.execute(
        f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchone()[0]
    names = cur.execute(
        f"SELECT name FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchall()
    filenames = cur.execute(
        f"SELECT teaser FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchall()

    cur.executemany(f"DELETE FROM {TBL_ITEMS} WHERE id = ?;", [(id,) for id in data])

    tbl_name = get_meta_table(cur, ds)
    cur.executemany(f"DELETE FROM {tbl_name} WHERE item_id = ?;", [(id,) for id in data])

    log_update(cur, TBL_ITEMS, ds)
    log_action(cur, "delete items", {"names": [n[0] for n in names]})

    for f in filenames:
        if f[0] is not None:
            base_path.joinpath(f[0]).unlink(missing_ok=True)
            backup_path.joinpath(f[0]).unlink(missing_ok=True)

    return cur


def get_item_expertise_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT ge.* FROM {TBL_EXPERTISE} ge LEFT JOIN {TBL_ITEMS} g ON ge.item_id = g.id WHERE g.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_item_expertise(cur, data):
    if len(data) == 0:
        return cur

    existing = []
    newones = []
    ds = None

    for d in data:
        e = cur.execute(
            f"SELECT id FROM {TBL_EXPERTISE} WHERE item_id = ? AND user_id = ?;",
            (d["item_id"], d["user_id"]),
        ).fetchone()
        if ds is None:
            ds = cur.execute(
                f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)
            ).fetchone()

        if e:
            d["id"] = e[0]
            existing.append(d)
        else:
            newones.append(d)

    if len(newones) > 0:
        item_names = cur.execute(
            f"SELECT name FROM {TBL_ITEMS} WHERE id IN ({make_space(len(newones))});",
            [d["item_id"] for d in newones],
        ).fetchall()
        user_names = cur.execute(
            f"SELECT name FROM {TBL_USERS} WHERE id IN ({make_space(len(newones))});",
            [d["user_id"] for d in newones],
        ).fetchall()

        cur.executemany(
            f"INSERT INTO {TBL_EXPERTISE} (item_id, user_id, value) VALUES (:item_id, :user_id, :value);",
            newones,
        )
        log_update(cur, TBL_EXPERTISE, ds[0])
        log_action(
            cur,
            "add expertise",
            {
                "data": [
                    [item_names[i][0], user_names[i][0], newones[i]["value"]]
                    for i in range(len(newones))
                ]
            },
        )

    if len(existing) > 0:
        update_item_expertise(cur, existing)

    return cur


def update_item_expertise(cur, data):
    if len(data) == 0:
        return cur

    item_names = cur.execute(
        f"SELECT name FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});",
        [d["item_id"] for d in data],
    ).fetchall()
    user_names = cur.execute(
        f"SELECT name FROM {TBL_USERS} WHERE id IN ({make_space(len(data))});",
        [d["user_id"] for d in data],
    ).fetchall()

    cur.executemany(
        f"UPDATE {TBL_EXPERTISE} SET value = ? WHERE id = ?;",
        [(d["value"], d["id"]) for d in data],
    )
    ds = cur.execute(
        f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id = ?;", (data[0]["item_id"],)
    ).fetchone()

    log_update(cur, TBL_EXPERTISE, ds[0])
    return log_action(
        cur,
        "update expertise",
        {
            "data": [
                [item_names[i][0], user_names[i][0], data[i]["value"]] for i in range(len(data))
            ]
        },
    )


def delete_item_expertise(cur, data):
    if len(data) == 0:
        return cur

    ds = cur.execute(
        f"SELECT i.dataset_id FROM {TBL_ITEMS} i LEFT JOIN {TBL_EXPERTISE} e ON i.id = e.item_id WHERE e.id = ?;",
        (data[0]["id"],),
    ).fetchone()
    cur.executemany(f"DELETE FROM {TBL_EXPERTISE} WHERE id = ?;", [(id,) for id in data])

    log_update(cur, TBL_EXPERTISE, ds[0])
    return log_action(cur, "delete expertise", {"count": cur.rowcount})

def has_user_by_id(cur, id):
    return cur.execute(f"SELECT id from {TBL_USERS} WHERE id = ?;", (id,)).fetchone() is not None
def has_user_by_name(cur, name):
    return cur.execute(f"SELECT id from {TBL_USERS} WHERE name = ?;", (name,)).fetchone() is not None

def get_user_by_name(cur, name):
    return cur.execute(f"SELECT id, name, role, email from {TBL_USERS} WHERE name = ?;", (name,)).fetchone()

def get_users_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT pu.dataset_id, u.id, u.name, u.role, u.email FROM {TBL_PRJ_USERS} pu FULL JOIN {TBL_USERS} u ON u.id = pu.user_id WHERE pu.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_users(cur):
    return cur.execute(f"SELECT id, name, role, email from {TBL_USERS};").fetchall()

def add_user_return_id(cur, d):
    if "name" not in d:
        return None

    ph = PasswordHasher()
    if "role" not in d or d["role"] is None or len(d["role"]) == 0:
        d["role"] = "collaborator"
    if "email" not in d or d["email"] is None or len(d["email"]) == 0:
        d["email"] = None

    if "pw_hash" not in d:
        if "password" in d and len(d["password"]) > 0:
            d["pw_hash"] = ph.hash(d["password"])
        else:
            d["pw_hash"] = ph.hash(d["name"])

    res = cur.execute(
        f"INSERT INTO {TBL_USERS} (name, role, email, login_id, pw_hash) VALUES (?,?,?,?,?) RETURNING id;",
        (d["name"], d["role"], d["email"], None, d["pw_hash"])
    ).fetchone()

    log_action(cur, "add user", { "name": d["name"] })
    return res["id"] if isinstance(res, dict) else res[0]

def add_users(cur, dataset, data):
    if len(data) == 0:
        return cur

    ph = PasswordHasher()

    for d in data:
        if "name" not in d:
            continue

        if "role" not in d:
            d["role"] = "collaborator"
        if "email" not in d:
            d["email"] = None
        if "pw_hash" not in d:
            d["pw_hash"] = ph.hash(d["name"])

        if "id" in d:
            cur.execute(
                f"INSERT INTO {TBL_USERS} (id, dataset_id, name, role, email, login_id, pw_hash) VALUES (?,?,?,?,?,?,?);",
                (d["id"], dataset, d["name"], d["role"], d["email"], None, d["pw_hash"])
            )
        else:
            cur.execute(
                f"INSERT INTO {TBL_USERS} (dataset_id, name, role, email, login_id, pw_hash) VALUES (?,?,?,?,?,?);",
                (dataset, d["name"], d["role"], d["email"], None, d["pw_hash"])
            )

    log_update(cur, TBL_USERS, dataset)
    return log_action(cur, "add users", {"names": [d["name"] for d in data]})



def has_project_user_by_id(cur, dataset, id):
    return cur.execute(f"SELECT id from {TBL_PRJ_USERS} WHERE dataset_id = ? AND user_id = ?;", (dataset, id)).fetchone() is not None

def add_users_to_project(cur, dataset, user_ids):
    if len(user_ids) == 0:
        return cur

    cur.executemany(
        f"INSERT INTO {TBL_PRJ_USERS} (user_id, dataset_id) VALUES (?, ?);",
        [(id, dataset) for id in user_ids],
    )

    log_update(cur, TBL_USERS, dataset)
    return log_action(cur, "add users", {"users": user_ids})


def get_codes_by_dataset(cur, dataset):
    return cur.execute(f"SELECT * from {TBL_CODES} WHERE dataset_id = ?;", (dataset,)).fetchall()


def add_code_return_id(cur, dataset, d):
    id = cur.execute(
        f"INSERT INTO {TBL_CODES} (dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?) RETURNING id;",
        (dataset, d["name"], d["description"], d["created"], d["created_by"]),
    ).fetchone()[0]

    log_update(cur, TBL_CODES, dataset)
    log_action(cur, "add codes", {"names": d["name"]}, d["created_by"])
    return id


def add_codes(cur, dataset, data):
    if len(data) == 0:
        return cur

    rows = []
    with_id = "id" in data[0]
    for d in data:
        if with_id:
            rows.append(
                (d["id"], dataset, d["name"], d["description"], d["created"], d["created_by"])
            )
        else:
            rows.append((dataset, d["name"], d["description"], d["created"], d["created_by"]))

    stmt = (
        f"INSERT INTO {TBL_CODES} (dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_CODES} (id, dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    )
    cur.executemany(stmt, rows)

    log_update(cur, TBL_CODES, dataset)
    return log_action(
        cur, "add codes", {"names": [d["name"] for d in data]}, data[0]["created_by"]
    )


def update_codes(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        rows.append((d["name"], d["description"], d["id"]))

    cur.executemany(f"UPDATE {TBL_CODES} SET name = ?, description = ? WHERE id = ?;", rows)

    log_update(cur, TBL_CODES, data[0]["dataset_id"])
    return log_action(
        cur, "update codes", {"names": [d["name"] for d in data]}, data[0]["created_by"]
    )


def get_tags_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT t.* from {TBL_TAGS} t LEFT JOIN {TBL_CODES} c ON t.code_id = c.id WHERE c.dataset_id = ? ORDER BY t.id;",
        (dataset,)
    ).fetchall()


def get_tags_by_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TAGS} WHERE code_id = ? ORDER BY id;", (code,)).fetchall()


def add_tag_return_id(cur, d):
    tag = add_tag_return_tag(cur, d)
    return tag.id


def add_tag_return_tag(cur, d):
    if "is_leaf" not in d or d["is_leaf"] is None:
        d["is_leaf"] = 1
    if "parent" not in d or d["parent"] is not None and d["parent"] < 1:
        d["parent"] = None
    if "description" not in d or len(d["description"]) == 0:
        d["description"] = d["name"]

    tag = cur.execute(
        f"INSERT INTO {TBL_TAGS} (code_id, name, description, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *;",
        (
            d["code_id"],
            d["name"],
            d["description"],
            d["created"],
            d["created_by"],
            d["parent"],
            d["is_leaf"],
        ),
    ).fetchone()

    if d["parent"] is not None:
        update_tags_is_leaf(cur, [d["parent"]])

    ds = cur.execute("SELECT dataset_id FROM codes WHERE id = ?;", (d["code_id"],)).fetchone()

    log_update(cur, TBL_TAGS, ds[0])
    log_action(cur, "add tag", {"name": d["name"]}, d["created_by"])
    return tag


def add_tags(cur, data):
    if len(data) == 0:
        return cur

    ids = []
    rows = []

    now = get_millis()

    datasets = set()

    for d in data:
        if "is_leaf" not in d or d["is_leaf"] is None:
            d["is_leaf"] = 1
        if "parent" not in d:
            d["parent"] = None
        if "description" not in d:
            d["description"] = None

        ds = cur.execute("SELECT dataset_id FROM codes WHERE id = ?;", (d["code_id"],)).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        if "id" in d:
            cur.execute(
                f"INSERT INTO {TBL_TAGS} (id, code_id, name, description, created, created_by, parent, is_leaf) VALUES (:id, :code_id, :name, :description, :created, :created_by, :parent, :is_leaf);",
                d,
            )
            ids.append(d["id"])
        else:
            tid = add_tag_return_id(cur, d)
            ids.append(tid)
            if d["parent"] is not None:
                ids.append(d["parent"])

        # get tag assignment for this tag for all transitions *from* this code
        trans = cur.execute(
            f"SELECT * FROM {TBL_TRANS} WHERE old_code = ?;", (d["code_id"],)
        ).fetchall()

        for t in trans:
            rows.append(
                {
                    "old_code": d["code_id"],
                    "new_code": t["new_code"],
                    "old_tag": ids[-1],
                    "new_tag": None,
                    "description": "ADDED TAG AFTERWARDS",
                    "created": now,
                }
            )

        # get tag assignment for this tag for all transitions *to* this code
        trans = cur.execute(
            f"SELECT * FROM {TBL_TRANS} WHERE new_code = ?;", (d["code_id"],)
        ).fetchall()

        for t in trans:
            rows.append(
                {
                    "old_code": t["old_code"],
                    "new_code": d["code_id"],
                    "old_tag": None,
                    "new_tag": ids[-1],
                    "description": "ADDED TAG AFTERWARDS",
                    "created": now,
                }
            )

    add_tag_assignments(cur, rows)

    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    log_action(cur, "add tags", {"names": [d["name"] for d in data]}, data[0]["created_by"])

    return update_tags_is_leaf(cur, ids)


def add_tags_for_assignment(cur, data):
    if len(data) == 0 or not "old_tag" in data[0]:
        return cur

    for d in data:
        if "is_leaf" not in d or d["is_leaf"] is None:
            d["is_leaf"] = 1
        if "parent" not in d:
            d["parent"] = None
        if "description" not in d:
            d["description"] = None

        tagNew = add_tag_return_tag(cur, d)
        tagOld = cur.execute(
            f"SELECT id from {TBL_TAGS} WHERE id = ?;", (d["old_tag"],)
        ).fetchone()

        if tagNew and tagOld:
            assigId = cur.execute(
                f"SELECT id FROM {TBL_TAG_ASS} WHERE old_tag = ?;", (tagOld[0],)
            ).fetchone()
            if assigId:
                update_tag_assignments(
                    cur,
                    [
                        {
                            "new_tag": tagNew[0]["id"],
                            "description": tagNew[0]["description"],
                            "id": assigId[0],
                        }
                    ],
                )

    return cur


def update_tags_is_leaf(cur, ids):
    if len(ids) == 0:
        return cur

    rows = []
    datasets = set()

    for id in ids:

        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        has_children = cur.execute(
            f"SELECT id FROM {TBL_TAGS} WHERE parent = ?;", (id,)
        ).fetchone()
        rows.append((0 if has_children else 1, id))

        my_parent = cur.execute(f"SELECT parent FROM {TBL_TAGS} WHERE id = ?;", (id,)).fetchone()
        if my_parent is not None:
            rows.append((0, my_parent[0]))

    # update is_leaf for all tags that where changed
    cur.executemany(f"UPDATE {TBL_TAGS} SET is_leaf = ? WHERE id = ?;", rows)
    names = cur.execute(
        f"SELECT name FROM {TBL_TAGS} WHERE id IN ({make_space(len(ids))});", ids
    ).fetchall()

    for d in datasets:
        log_update(cur, TBL_TAGS, d)
    return log_action(cur, "update tags", {"names": [n[0] for n in names]})


def update_tags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    tocheck = []
    datasets = set()

    for d in data:
        if "parent" not in d:
            d["parent"] = None
        if d["parent"] is not None and d["parent"] < 0:
            d["parent"] = None

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        rows.append((d["name"], d["description"], d["parent"], d["is_leaf"], d["id"]))

        tocheck.append(d["id"])
        if d["parent"] is not None:
            tocheck.append(d["parent"])

    cur.executemany(
        f"UPDATE {TBL_TAGS} SET name = ?, description = ?, parent = ?, is_leaf = ? WHERE id = ?;",
        rows,
    )
    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    log_action(cur, "update tags", {"names": [d["name"] for d in data]})
    # update is_leaf for all tags that where changed
    return update_tags_is_leaf(cur, tocheck)


def group_tags(cur, parent, data):
    if len(data) == 0:
        return cur

    log_action(
        cur, "merge tags", {"parent": parent["name"], "children": [d["name"] for d in data]}
    )
    id = add_tag_return_id(cur, parent)

    for d in data:
        d["parent"] = id

    return update_tags(cur, data)


def split_tags(cur, data):
    if len(data) == 0:
        return cur

    for d in data:
        if "names" not in d:
            continue

        tag = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?;", (d["id"],)).fetchone()
        assigsOLD = cur.execute(
            f"SELECT * FROM {TBL_TAG_ASS} WHERE old_code = ? AND old_tag = ?",
            (tag.code_id, d["id"]),
        ).fetchall()
        assigsNEW = cur.execute(
            f"SELECT * FROM {TBL_TAG_ASS} WHERE new_code = ? AND new_tag = ?",
            (tag.code_id, d["id"]),
        ).fetchall()

        children = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE parent = ?;", (d["id"],)
        ).fetchall()
        first = None

        to_assign = d["assignments"] if "assignments" in d else None
        use_assign = to_assign is not None

        log_action(cur, "split tag", {"name": tag.name})

        ids = {}

        for n in d["names"]:

            # create and save new tag
            new_tag = add_tag_return_id(
                cur,
                {
                    "name": n,
                    "description": f"split from tag {tag.name} with description:\n{tag.description}",
                    "code_id": tag.code_id,
                    "created": d["created"],
                    "created_by": d["created_by"],
                    "parent": tag.parent,
                    "is_leaf": tag.is_leaf,
                },
            )

            ids[n] = new_tag

            if first is None:
                first = new_tag

            rows = []
            # update tag assignments
            for a in assigsOLD:
                c = a._asdict()
                c["old_tag"] = new_tag
                del c["id"]
                rows.append(c)
            for a in assigsNEW:
                c = a._asdict()
                c["new_tag"] = new_tag
                del c["id"]
                rows.append(c)

            add_tag_assignments(cur, rows)

        rows = []
        dts = get_datatags_by_tag(cur, d["id"])
        for dt in dts:
            c = dt._asdict()
            if use_assign:
                tag_name = [d for d in to_assign if d["id"] == c["item_id"]][0]["tag"]
                c["tag_id"] = ids[tag_name]
            else:
                c["tag_id"] = first[0]
            rows.append(c)

            # update evidence for this tag+item
            cur.execute(
                f"UPDATE {TBL_EVIDENCE} SET tag_id = ? WHERE code_id = ? AND tag_id = ? AND item_id = ?;",
                (c["tag_id"], tag.code_id, d["id"], c["item_id"]),
            )

            # update externalization tags for this tag+item
            exts = cur.execute(
                f"SELECT e.* FROM {TBL_META_ITEMS} e LEFT JOIN {TBL_META_GROUPS} eg ON e.group_id = eg.id WHERE eg.code_id = ? AND eg.item_id = ?;",
                (tag.code_id, c["item_id"]),
            ).fetchall()

            for e in exts:
                cur.execute(
                    f"UPDATE {TBL_META_CON_TAG} SET tag_id = ? WHERE meta_id = ? AND tag_id = ?;",
                    [c["tag_id"], e.id, d["id"]],
                )

        # update datatags
        update_datatags(cur, rows)

        if first is not None:
            rows = []
            # update parent reference
            for t in children:
                c = t._asdict()
                c["parent"] = first[0]
                rows.append(c)

            update_tags(cur, rows)

        # delete tag that is being split
        delete_tags(cur, [d["id"]])

        # delete old tag assignments (if still present)
        delete_tag_assignments(cur, [a.id for a in assigsOLD])
        delete_tag_assignments(cur, [a.id for a in assigsNEW])

    return cur


def get_highest_parent(cur, ids):
    if len(ids) == 0:
        return cur

    tags = cur.execute(
        f"SELECT * FROM {TBL_TAGS} WHERE id IN ({make_space(len(ids))});", ids
    ).fetchall()
    max_height = 0
    max_id = -1

    parent_ids = [t["parent"] for t in tags if t["parent"] is not None]
    parents = cur.execute(
        f"SELECT * FROM {TBL_TAGS} WHERE id IN ({make_space(len(parent_ids))});", parent_ids
    ).fetchall()

    for t in parents:
        # only look at parent not part of the set
        if t["id"] not in ids:
            tmp = t
            height = 1
            while tmp["parent"] is not None:
                tmp = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?;", (tmp["parent"],))
                height += 1

            if height > max_height:
                max_height = height
                max_id = t["id"]

    return max_id


def merge_tags(cur, data):
    if len(data) == 0:
        return cur

    for d in data:
        if "ids" not in d:
            continue

        tags = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE id IN ({make_space(len(d['ids']))});", d["ids"]
        ).fetchall()
        parent = d["parent"] if "parent" in d else get_highest_parent(cur, d["ids"])

        log_action(cur, "merge tags", {"names": [t.name for t in tags]})

        if "description" not in d or len(d["description"]) == 0:
            d["description"] = f"merge tags:\n{', '.join([t.name for t in tags])}"

        obj = {
            "name": "_TMP_MERGE_TAG_",
            "description": d["description"],
            "code_id": d["code_id"],
            "created": d["created"],
            "created_by": d["created_by"],
            "parent": parent,
            "is_leaf": 1 if all([t.is_leaf == 1 for t in tags]) else 0,
        }
        new_tag = add_tag_return_tag(cur, obj)

        for t in tags:
            assigsOLD = cur.execute(
                f"SELECT * FROM {TBL_TAG_ASS} WHERE old_code = ? AND old_tag = ?;",
                (t.code_id, t.id),
            ).fetchall()
            assigsNEW = cur.execute(
                f"SELECT * FROM {TBL_TAG_ASS} WHERE new_code = ? AND new_tag = ?;",
                (t.code_id, t.id),
            ).fetchall()

            rows = []
            # update tag assignments
            for a in assigsOLD:
                c = a._asdict()
                c["old_tag"] = new_tag.id
                del c["id"]
                rows.append(c)
            for a in assigsNEW:
                c = a._asdict()
                c["new_tag"] = new_tag.id
                del c["id"]
                rows.append(c)

            add_tag_assignments(cur, rows)

            delete_tag_assignments(cur, [a.id for a in assigsOLD])
            delete_tag_assignments(cur, [a.id for a in assigsNEW])

        rows = []
        children = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE parent IN ({make_space(len(tags))});", d["ids"]
        ).fetchall()
        for t in children:
            c = t._asdict()
            c["parent"] = new_tag.id
            rows.append(c)

        # update child tags
        update_tags(cur, rows)

        rows = []
        dts = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE tag_id IN ({make_space(len(tags))});", d["ids"]
        ).fetchall()
        for dt in dts:
            c = dt._asdict()
            c["tag_id"] = new_tag.id
            del c["id"]
            rows.append(c)

        # create new datatags
        add_datatags(cur, rows)

        # update evidence
        cur.execute(
            f"UPDATE {TBL_EVIDENCE} SET tag_id = ? WHERE code_id = ? AND tag_id IN ({make_space(len(tags))});",
            [new_tag.id, d["code_id"]] + d["ids"],
        )

        # update externalization tags
        exts = get_meta_items_by_code(cur, d["code_id"])
        for e in exts:
            cur.execute(
                f"UPDATE {TBL_META_CON_TAG} SET tag_id = ? WHERE item_id = ? AND tag_id IN ({make_space(len(tags))});",
                [new_tag.id, e.id] + d["ids"],
            )

        # delete tags that were merged
        delete_tags(cur, d["ids"])

        # rename new tag
        obj["name"] = d["name"]
        obj["id"] = new_tag.id
        update_tags(cur, [obj])

    return cur


def delete_tags(cur, ids):
    if len(ids) == 0:
        return cur

    tocheck = []
    datasets = set()

    for id in ids:
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        my_parent = cur.execute(f"SELECT parent FROM {TBL_TAGS} WHERE id = ?;", (id,)).fetchone()
        children = cur.execute(
            f"SELECT id, name FROM {TBL_TAGS} WHERE parent = ?;", (id,)
        ).fetchall()
        if my_parent is not None:
            tocheck.append(my_parent[0])

        # remove this node as parent
        cur.executemany(
            f"UPDATE {TBL_TAGS} SET parent = ? WHERE id = ?;",
            [(my_parent[0], t[0]) for t in children],
        )
        log_action(cur, "update tags", {"names": [d[1] for d in children]})

    id_tuples = [(id,) for id in ids]
    names = cur.execute(
        f"SELECT name FROM {TBL_TAGS} WHERE id IN ({make_space(len(ids))});", ids
    ).fetchall()

    cur.executemany(f"DELETE FROM {TBL_TAGS} WHERE id = ?;", id_tuples)
    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    log_action(cur, "delete tags", {"names": [n[0] for n in names]})

    # remove tag assignments for tags
    cur.executemany(
        f"DELETE FROM {TBL_TAG_ASS} WHERE old_tag = ? OR new_tag = ?;", [(id, id) for id in ids]
    )
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_TAG_ASS, d)
        log_action(cur, "delete tag assignments", {"count": cur.rowcount})

    # remove externalization connections to tags if tags are deleted
    cur.executemany(f"DELETE FROM {TBL_META_CON_TAG} WHERE tag_id = ?;", id_tuples)
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_TAG, d)
        log_action(cur, "delete meta tag connections", {"count": cur.rowcount})

    # set tag id to null for evidence that references these tags
    cur.executemany(
        f"UPDATE {TBL_EVIDENCE} SET tag_id = ? WHERE tag_id = ?;", [(None, id) for id in ids]
    )
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_EVIDENCE, d)
        log_action(cur, "update evidence", {"count": cur.rowcount})

    return update_tags_is_leaf(cur, tocheck)


def get_datatags_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT dt.* FROM {TBL_DATATAGS} dt LEFT JOIN {TBL_CODES} c ON dt.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_datatags_by_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_DATATAGS} WHERE code_id = ?;", (code,)).fetchall()


def get_datatags_by_tag(cur, tag):
    return cur.execute(f"SELECT * from {TBL_DATATAGS} WHERE tag_id = ?;", (tag,)).fetchall()


def get_datatags_by_item(cur, item):
    return cur.execute(f"SELECT * from {TBL_DATATAGS} WHERE item_id = ?;", (item,)).fetchall()


def add_datatags(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    log_data = []
    with_id = "id" in data[0]
    datasets = set()

    for d in data:
        if with_id:
            rows.append(
                (d["id"], d["item_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"])
            )
        else:
            rows.append((d["item_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"]))

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        log_data.append([
            one_or_none(cur, f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)),
            one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],)),
            one_or_none(cur, f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],))
        ])

    stmt = (
        f"INSERT OR IGNORE INTO {TBL_DATATAGS} (item_id, tag_id, code_id, created, created_by) VALUES (?, ? , ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_DATATAGS} (id, item_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    )
    cur.executemany(stmt, rows)

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "add datatags", {"data": log_data})


def update_datatags(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()

    for d in data:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON t.code_id = c.id WHERE t.id = ?;",
            (d["tag_id"],),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

    cur.executemany(
        f"UPDATE {TBL_DATATAGS} SET tag_id = ? WHERE id = ?;",
        [(d["tag_id"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "update datatags", {"count": cur.rowcount})


def update_item_datatags(cur, data):
    code_id = data["code_id"]
    user_id = data["user_id"]
    item_id = data["item_id"]
    created = data["created"]

    print(code_id)

    ds = cur.execute(f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (code_id,)).fetchone()[0]

    item_name = cur.execute(f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (item_id,)).fetchone()[
        0
    ]
    user_name = cur.execute(f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (user_id,)).fetchone()[
        0
    ]

    # remove datatags not in the list
    tokeep = [int(d["tag_id"]) for d in data["tags"] if "tag_id" in d]
    results = cur.execute(
        f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ? AND created_by = ?;",
        (item_id, code_id, user_id),
    )
    existing = [d[0] for d in results.fetchall()]
    toremove = np.setdiff1d(np.array(existing), np.array(tokeep)).tolist()

    if len(toremove) > 0:
        cur.executemany(
            f"DELETE FROM {TBL_DATATAGS} WHERE created_by = ? AND id = ?;",
            [(user_id, tid) for tid in toremove],
        )
        if cur.rowcount > 0:
            log_update(cur, TBL_DATATAGS, ds)
            log_action(cur, "delete datatags", {"count": cur.rowcount}, user_id)

    # add datatags where tags already exist in the database
    toadd = np.setdiff1d(np.array(tokeep), np.array(existing)).tolist()

    if len(toadd) > 0:
        stmt = f"INSERT INTO {TBL_DATATAGS} (item_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
        log_data = []
        for d in toadd:
            log_data.append(
                cur.execute(f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (int(d),)).fetchone()[0]
            )

        cur.executemany(stmt, [(item_id, int(d), code_id, created, user_id) for d in toadd])
        log_update(cur, TBL_DATATAGS, ds)
        log_action(
            cur, "add datatags", {"tags": log_data, "item": item_name, "user": user_name}, user_id
        )

    # add tags that do not exist in the database
    newtags = [d["tag_name"] for d in data["tags"] if "tag_name" in d]
    newtags_desc = [d["description"] for d in data["tags"] if "tag_name" in d]

    if len(newtags) > 0:
        stmt = f"INSERT INTO {TBL_TAGS} (name, description, code_id, created, created_by, parent, is_leaf) VALUES (?, ?, ?, ?, ?, ?, ?);"
        rows = []
        for i, d in enumerate(newtags):
            rows.append((d, newtags_desc[i], code_id, created, user_id, None, 1))
        # add new tags
        add_tags(cur, rows)

        result = cur.execute(
            f"SELECT id FROM {TBL_TAGS} WHERE created_by = ? AND name IN ({make_space(len(newtags))});",
            [user_id] + newtags,
        ).fetchall()
        new_tag_ids = [d[0] for d in result]

        # add datatags for new these tags
        if len(new_tag_ids) > 0:
            stmt = f"INSERT INTO {TBL_DATATAGS} (item_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
            cur.executemany(stmt, [(item_id, d, code_id, created, user_id) for d in new_tag_ids])
            log_data = []
            for d in toadd:
                log_data.append(
                    cur.execute(
                        f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (int(d),)
                    ).fetchone()[0]
                )
            log_action(
                cur,
                "add datatags",
                {"tags": log_data, "item": item_name, "user": user_name},
                user_id,
            )

    return cur


def delete_datatags(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON t.code_id = c.id "
            + f"LEFT JOIN {TBL_DATATAGS} dt ON t.id = dt.tag_id WHERE dt.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

    cur.executemany(f"DELETE FROM {TBL_DATATAGS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "delete datatags", {"count": cur.rowcount})


def get_evidence_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT e.* from {TBL_EVIDENCE} e LEFT JOIN {TBL_ITEMS} g ON e.item_id = g.id WHERE g.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_evidence_by_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_EVIDENCE} WHERE code_id = ?;", (code,)).fetchall()


def get_evidence_by_tag(cur, tag):
    return cur.execute(f"SELECT * from {TBL_EVIDENCE} WHERE tag_id = ?;", (tag,)).fetchall()


def add_evidence(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    log_data = []
    with_id = "id" in data[0]
    datasets = set()

    for d in data:

        if "filepath" not in d:
            d["filepath"] = None
        if "tag_id" not in d:
            d["tag_id"] = None

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        if with_id:
            rows.append(
                (
                    d["id"],
                    d["item_id"],
                    d["code_id"],
                    d["tag_id"],
                    d["filepath"],
                    d["description"],
                    d["created"],
                    d["created_by"],
                )
            )
        else:
            rows.append(
                (
                    d["item_id"],
                    d["code_id"],
                    d["tag_id"],
                    d["filepath"],
                    d["description"],
                    d["created"],
                    d["created_by"],
                )
            )

        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)
                ).fetchone()[0],
                (
                    cur.execute(
                        f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],)
                    ).fetchone()[0]
                    if d["tag_id"] is not None
                    else None
                ),
                cur.execute(
                    f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)
                ).fetchone()[0],
            ]
        )

    stmt = (
        f"INSERT INTO {TBL_EVIDENCE} (item_id, code_id, tag_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_EVIDENCE} (id, item_id, code_id, tag_id, filepath, description, created, created_by) VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
    )
    cur.executemany(stmt, rows)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)
    return log_action(cur, "add evidence", {"data": log_data})


def add_evidence_return_id(cur, d):
    if "filepath" not in d:
        d["filepath"] = None
    if "tag_id" not in d:
        d["tag_id"] = None

    log_data = [
        cur.execute(f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)).fetchone()[0],
        (
            cur.execute(f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],)).fetchone()[0]
            if d["tag_id"] is not None
            else None
        ),
        cur.execute(f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)).fetchone()[
            0
        ],
    ]

    cur = cur.execute(
        f"INSERT INTO {TBL_EVIDENCE} (item_id, code_id, tag_id, filepath, description, created, created_by) VALUES (:item_id, :code_id, :tag_id, :filepath, :description, :created, :created_by) RETURNING id;",
        d,
    )
    id = next(cur)[0]

    ds = cur.execute(
        f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
    ).fetchone()[0]

    log_update(cur, TBL_EVIDENCE, ds)
    log_action(cur, "add evidence", {"data": [log_data]})

    return id


def update_evidence(cur, data, base_path, backup_path):
    if len(data) == 0:
        return

    before = cur.execute(
        f"SELECT filepath FROM {TBL_EVIDENCE} WHERE id IN ({make_space(len(data))});",
        [d["id"] for d in data],
    ).fetchall()

    rows = []
    datasets = set()

    for r in data:
        if "filepath" not in r:
            r["filepath"] = None
        if "tag_id" not in r:
            r["tag_id"] = None

        ds = get_dataset_id_by_code(cur, r["code_id"])
        if ds is not None:
            datasets.add(ds)

        rows.append((r["description"], r["filepath"], r["tag_id"], r["id"]))

    cur.executemany(
        f"UPDATE {TBL_EVIDENCE} SET description = ?, filepath = ?, tag_id = ? WHERE id = ?;", rows
    )

    for d in before:
        if d[0] is not None:
            has = cur.execute(f"SELECT id FROM {TBL_EVIDENCE} WHERE filepath = ?;", d).fetchone()
            if has is None:
                base_path.joinpath(d[0]).unlink(missing_ok=True)
                backup_path.joinpath(d[0]).unlink(missing_ok=True)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "update evidence", {"count": cur.rowcount})


def delete_evidence(cur, ids, base_path, backup_path):
    if len(ids) == 0:
        return cur

    datasets = set()
    for id in ids:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_EVIDENCE} e ON c.id = e.code_id WHERE e.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

    filenames = cur.execute(
        f"SELECT filepath FROM {TBL_EVIDENCE} WHERE id IN ({make_space(len(ids))});", ids
    ).fetchall()
    cur.executemany(f"DELETE FROM {TBL_EVIDENCE} WHERE id = ?;", [(id,) for id in ids])

    for f in filenames:
        if f is not None and f[0] is not None:
            has = cur.execute(f"SELECT id FROM {TBL_EVIDENCE} WHERE filepath = ?;", f).fetchone()
            if has is None:
                base_path.joinpath(f[0]).unlink(missing_ok=True)
                backup_path.joinpath(f[0]).unlink(missing_ok=True)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "delete evidence", {"count": cur.rowcount})


def get_tag_assignments_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT ta.* from {TBL_TAG_ASS} ta LEFT JOIN codes c ON ta.old_code = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_tag_assignments_by_old_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TAG_ASS} WHERE old_code = ?;", (code,)).fetchall()


def get_tag_assignments_by_new_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TAG_ASS} WHERE new_code = ?;", (code,)).fetchall()


def get_tag_assignments_by_codes(cur, old_code, new_code):
    return cur.execute(
        f"SELECT * from {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ?;", (old_code, new_code)
    ).fetchall()


def add_tag_assignments(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:

        existingOld = cur.execute(
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ? AND old_tag = ? AND new_tag = NULL;",
            (d["old_code"], d["new_code"], d["old_tag"]),
        ).fetchone()
        existingNew = cur.execute(
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ? AND old_tag = NULL AND new_tag = ?;",
            (d["old_code"], d["new_code"], d["new_tag"]),
        ).fetchone()

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        if d["old_tag"] is not None and existingOld and d["new_tag"] is not None and existingNew:
            o1 = d.copy()
            o1["id"] = existingOld[0]
            o1["new_tag"] = d["new_tag"]
            o2 = d.copy()
            o2["id"] = existingNew[0]
            o2["old_tag"] = d["old_tag"]
            update_tag_assignments(cur, [o1, o2])
            continue

        if "id" in d:
            cur.execute(
                f"INSERT OR IGNORE INTO {TBL_TAG_ASS} (id, old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (
                    d["id"],
                    d["old_code"],
                    d["new_code"],
                    d["old_tag"],
                    d["new_tag"],
                    d["description"],
                    d["created"],
                ),
            )
        else:
            cur.execute(
                f"INSERT OR IGNORE INTO {TBL_TAG_ASS} (old_code, new_code, old_tag, new_tag, description, created) VALUES (?, ?, ?, ?, ?, ?);",
                (
                    d["old_code"],
                    d["new_code"],
                    d["old_tag"],
                    d["new_tag"],
                    d["description"],
                    d["created"],
                ),
            )

        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
                ).fetchone()[0],
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["new_code"],)
                ).fetchone()[0],
                (
                    cur.execute(
                        f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["old_tag"],)
                    ).fetchone()[0]
                    if d["old_tag"] is not None
                    else None
                ),
                (
                    cur.execute(
                        f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["new_tag"],)
                    ).fetchone()[0]
                    if d["new_tag"] is not None
                    else None
                ),
            ]
        )

    remove_invalid_tag_assignments(cur)
    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "add tag assignments", {"data": log_data})


def update_tag_assignments(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    log_data = []
    datasets = set()

    for d in data:
        rows.append((d["new_tag"], d["description"], d["id"], d["old_code"], d["new_code"]))

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
                ).fetchone()[0],
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["new_code"],)
                ).fetchone()[0],
                cur.execute(
                    f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["old_tag"],)
                ).fetchone()[0],
                cur.execute(
                    f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["new_tag"],)
                ).fetchone()[0],
            ]
        )

    cur.executemany(
        f"UPDATE {TBL_TAG_ASS} SET new_tag = ?, description = ? WHERE id = ? AND old_code = ? AND new_code = ?;",
        rows,
    )
    remove_invalid_tag_assignments(cur)

    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "update tag assignments", {"data": log_data})


def delete_tag_assignments(cur, ids):
    if len(ids) == 0:
        return cur

    datasets = set()
    for id in ids:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAG_ASS} t ON WHERE c.id = t.old_code WHERE t.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

    cur.executemany(f"DELETE FROM {TBL_TAG_ASS} WHERE id = ?;", [(id,) for id in ids])
    remove_invalid_tag_assignments(cur)

    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "delete tag assignments", {"count": cur.rowcount})


def remove_invalid_tag_assignments(cur):
    return cur.execute(f"DELETE FROM {TBL_TAG_ASS} WHERE old_tag = NULL AND new_code = NULL;")


def get_code_transitions_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT ct.* from {TBL_TRANS} ct LEFT JOIN codes c ON ct.old_code = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_code_transitions_by_old_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TRANS} WHERE old_code = ?;", (code,)).fetchall()


def get_code_transitions_by_new_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TRANS} WHERE new_code = ?;", (code,)).fetchall()


def get_code_transitions_by_codes(cur, old_code, new_code):
    return cur.execute(
        f"SELECT * from {TBL_TRANS} WHERE old_code = ? AND new_code = ?;",
        (old_code, new_code),
    ).fetchall()


def add_code_transitions(cur, data):
    if len(data) == 0:
        return cur

    rows = []
    log_data = []
    datasets = set()
    with_id = "id" in data[0]

    for d in data:
        if "finished" not in d:
            d["finished"] = None

        ds_old = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
        ).fetchone()
        ds_new = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["new_code"],)
        ).fetchone()
        if ds_old is None or ds_new is None or ds_old[0] != ds_new[0]:
            raise ValueError("incompatible or missing codes")
        else:
            datasets.add(ds_old[0])

        if with_id:
            rows.append((d["id"], d["old_code"], d["new_code"], d["started"], d["finished"]))
        else:
            rows.append((d["old_code"], d["new_code"], d["started"], d["finished"]))

        log_data.append(
            [
                cur.execute(f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],))
                .fetchone()
                .name,
                cur.execute(f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["new_code"],))
                .fetchone()
                .name,
            ]
        )

    stmt = (
        f"INSERT INTO {TBL_TRANS} (old_code, new_code, started, finished) VALUES (?, ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_TRANS} (id, old_code, new_code, started, finished) VALUES (?, ?, ?, ?, ?);"
    )

    cur.executemany(stmt, rows)

    for d in datasets:
        log_update(cur, TBL_TRANS, d)

    return log_action(cur, "add code transitions", {"data": log_data})


def update_code_transitions(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:
        ds_old = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
        ).fetchone()
        datasets.add(ds_old[0])

        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
                ).fetchone()[0],
                cur.execute(
                    f"SELECT name FROM {TBL_CODES} WHERE id = ?;", (d["new_code"],)
                ).fetchone()[0],
            ]
        )

    cur.executemany(
        f"UPDATE {TBL_TRANS} SET finished = ? WHERE id = ?;",
        [(d["finished"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_TRANS, d)
    return log_action(cur, "update code transitions", {"data": log_data})


def delete_code_transitions(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TRANS} t ON c.id = t.old_code WHERE t.id = ?;",
            (id,),
        )
        if ds is not None:
            datasets.add(ds[0])

    cur.executemany(f"DELETE FROM {TBL_TRANS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_TRANS, d)

    return log_action(cur, "delete code transitions", {"count": cur.rowcount})


def prepare_transition(cur, old_code, new_code):
    ds_old = cur.execute(
        f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (old_code,)
    ).fetchone()
    ds_new = cur.execute(
        f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (new_code,)
    ).fetchone()

    if ds_old is None or ds_new is None or ds_old[0] != ds_new[0]:
        raise ValueError("incompatible or missing codes")

    log_action(cur, "prepare code transitions", {"old": old_code, "new": new_code})

    old_tags = get_tags_by_code(cur, old_code)
    assigned = {}

    rows = []
    print("preparing transition")
    # create/copy tags from old code that do not have a parent
    for t in old_tags:

        # check if a tag assignment alraady exists
        cur.execute(
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ? AND old_tag = ?;",
            (old_code, new_code, t.id),
        )
        tag_assigned_id = cur.fetchone()

        # if the old tag already has an assignment we dont need to create a new tag
        if tag_assigned_id is not None:
            assigned[t.id] = tag_assigned_id[0]
            print("\t", "tag", t.name, "is already assigned")
            continue

        # no assignemnt - but check if new tag with same name already exists
        cur.execute(
            f"SELECT id FROM {TBL_TAGS} WHERE code_id = ? AND name = ?;", (new_code, t.name)
        )
        exists = cur.fetchone() is not None

        if not exists:
            new_tag = add_tag_return_tag(
                cur,
                {
                    "code_id": new_code,
                    "name": t.name,
                    "description": t.description,
                    "created": t.created,
                    "created_by": t.created_by,
                    "parent": None,
                    "is_leaf": t.is_leaf,
                },
            )
            assigned[t.id] = new_tag.id

    new_tags = get_tags_by_code(cur, new_code)

    for t in old_tags:
        has_assigned = assigned[t.id] if t.id in assigned else None

        # find matching new tag
        tNew = [
            tag
            for tag in new_tags
            if has_assigned is not None and tag.id == has_assigned or tag.name == t.name
        ]

        if len(tNew) == 0:
            print("ERROR")
            print("missing tag", t.name)
            raise Exception("missing tag " + t.name)

        # check if tag assignment already exists
        cur.execute(
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ? AND old_tag = ?;",
            (old_code, new_code, t.id),
        )
        exists = cur.fetchone() is not None

        if not exists:
            add_tag_assignments(
                cur,
                [
                    {
                        "old_code": old_code,
                        "new_code": new_code,
                        "old_tag": t.id,
                        "new_tag": tNew[0].id,
                        "created": tNew[0].created,
                        "description": "INITIAL COPY",
                    }
                ],
            )

        rows = []

        # get datatags in old code
        datatags = get_datatags_by_tag(cur, t.id)
        for d in datatags:

            # check if datatag already exists
            cur.execute(
                f"SELECT id FROM {TBL_DATATAGS} WHERE code_id = ? AND item_id = ? AND tag_id = ? AND created_by = ?;",
                (new_code, d.item_id, tNew[0].id, d.created_by),
            )
            exists = cur.fetchone() is not None

            if not exists:
                rows.append(
                    {
                        "item_id": d.item_id,
                        "tag_id": tNew[0].id,
                        "code_id": new_code,
                        "created": d.created,
                        "created_by": d.created_by,
                    }
                )

        # add datatags to new code
        add_datatags(cur, rows)

        if t.parent is not None:
            pTag = [tag for tag in old_tags if tag.id == t.parent][0]

            has_assigned_p = assigned[pTag.id] if pTag.id in assigned else None

            # find matching new parent tag
            tNewParent = [
                tag
                for tag in new_tags
                if has_assigned_p is not None and tag.id == has_assigned_p or tag.name == pTag.name
            ]

            if len(tNewParent) == 0:
                print("ERROR")
                print("missing tag parent", pTag.name)
                raise Exception("missing tag parent " + pTag.name)

            update_tags(
                cur,
                [
                    {
                        "name": tNew[0].name,
                        "description": tNew[0].description,
                        "parent": tNewParent[0].id,
                        "is_leaf": tNew[0].is_leaf,
                        "id": tNew[0].id,
                        "code_id": new_code,
                    }
                ],
            )

    # get evidence for old code
    ev = get_evidence_by_code(cur, old_code)

    assigned_evs = {}

    num = 0
    for d in ev:
        # check if evidence already exists
        cur.execute(
            f"SELECT id FROM {TBL_EVIDENCE} WHERE item_id = ? AND description = ? AND created_by = ? AND tag_id = ? AND filepath = ? AND code_id = ?;",
            (d.item_id, d.description, d.created_by, d.tag_id, d.filepath, new_code),
        )
        result = cur.fetchone()
        exists = result is not None

        if exists:
            assigned_evs[d.id] = result.id
        else:
            obj = {
                "item_id": d.item_id,
                "code_id": new_code,
                "filepath": d.filepath,
                "description": d.description,
                "created": d.created,
                "created_by": d.created_by,
            }
            # if evidence has tag, find the assigned tag in the new code
            if d.tag_id is not None and d.tag_id in assigned:
                obj["tag_id"] = assigned[d.tag_id]

            # add evidence for old code
            assigned_evs[d.id] = add_evidence_return_id(cur, obj)
            num += 1

    print(f"added {num} evidence")

    assigned_cats = {}

    ext_cats = get_meta_categories_by_code(cur, old_code)

    for d in ext_cats:

        pname = (
            cur.execute(f"SELECT name FROM {TBL_META_CATS} WHERE id = ?;", (d.parent,)).fetchone()
            if d.parent
            else None
        )
        # check if externalization category already exists
        if pname:
            cur.execute(
                f"SELECT ec1.id FROM {TBL_META_CATS} ec1 INNER JOIN {TBL_META_CATS} ec2 ON ec1.parent = ec2.id WHERE ec2.name = ? AND ec1.name = ? AND ec1.created_by = ? AND ec1.code_id = ?;",
                (pname[0], d.name, d.created_by, new_code),
            )
        else:
            cur.execute(
                f"SELECT id FROM {TBL_META_CATS} WHERE name = ? AND created_by = ? AND parent = ? AND code_id = ?;",
                (d.name, d.created_by, d.parent, new_code),
            )

        result = cur.fetchone()
        exists = result is not None

        if exists:
            assigned_cats[d.id] = result.id
        else:
            new_cat = add_meta_category_return_id(
                cur,
                {
                    "name": d.name,
                    "description": d.description,
                    "created": t.created,
                    "created_by": t.created_by,
                    "parent": None,
                    "dataset_id": d.dataset_id,
                    "code_id": new_code,
                },
            )
            assigned_cats[d.id] = new_cat

    for d in ext_cats:

        has_assigned = assigned_cats[d.id] if d.id in assigned_cats else None

        if d.parent is not None:
            has_assigned_p = assigned_cats[d.parent] if d.parent in assigned_cats else None

            if has_assigned is not None and has_assigned_p is not None:
                # update parent
                cur.execute(
                    f"UPDATE {TBL_META_CATS} SET parent = ? WHERE id = ?;",
                    (has_assigned_p, has_assigned),
                )

    # get externalization groups for old code
    ext_groups = get_meta_groups_by_code(cur, old_code)

    num = 0
    for g in ext_groups:

        # get externalizations for old code
        exts = cur.execute(
            f"SELECT * FROM {TBL_META_ITEMS} WHERE group_id = ?;", (g.id,)
        ).fetchall()

        group_id = None
        existing = []
        numMissing = 0

        for d in exts:

            # check if externalization already exists
            cur.execute(
                f"SELECT e.group_id FROM {TBL_META_ITEMS} e LEFT JOIN {TBL_META_GROUPS} eg ON e.group_id = eg.id WHERE e.name = ? AND e.description = ? AND e.created_by = ? AND eg.code_id = ? AND eg.item_id = ?;",
                (d.name, d.description, d.created_by, new_code, g.item_id),
            )
            result = cur.fetchone()
            existing_id = result.group_id if result is not None else None
            existing.append(existing_id is None)

            if existing_id is not None:
                group_id = existing_id
            else:
                numMissing += 1

        # if there are externalizations missing, add them
        if numMissing > 0:
            # if there is no group yet, create one
            if group_id is None:
                as_obj = {
                    "item_id": g.item_id,
                    "code_id": new_code,
                    "created": g.created,
                    "created_by": g.created_by,
                }
                group_id = add_meta_group_return_id(cur, as_obj)

            rows = []

            for i, d in enumerate(exts):

                if existing[i]:

                    obj = {
                        "name": d.name,
                        "group_id": group_id,
                        "description": d.description,
                        "cluster": d.cluster,
                        "code_id": new_code,
                        "created": d.created,
                        "created_by": d.created_by,
                        "tags": [],
                        "categories": [],
                        "evidence": [],
                    }

                    tags = cur.execute(
                        f"SELECT * FROM {TBL_META_CON_TAG} WHERE meta_id = ?;", (d.id,)
                    ).fetchall()
                    # if externalization has tags
                    if len(tags) > 0:
                        for t in tags:
                            if t.tag_id in assigned:
                                obj["tags"].append({"tag_id": assigned[t.tag_id]})

                    cats = cur.execute(
                        f"SELECT * FROM {TBL_META_CON_CAT} WHERE meta_id = ?;", (d.id,)
                    ).fetchall()
                    # if externalization has categories
                    if len(cats) > 0:
                        for c in cats:
                            if c.cat_id in assigned_cats:
                                obj["categories"].append({"cat_id": assigned_cats[c.cat_id]})

                    evs = cur.execute(
                        f"SELECT * FROM {TBL_META_CON_EV} WHERE meta_id = ?;", (d.id,)
                    ).fetchall()
                    # if externalization has categories
                    if len(evs) > 0:
                        for e in evs:
                            if e.ev_id in assigned_evs:
                                obj["evidence"].append({"ev_id": assigned_evs[e.ev_id]})

                    rows.append(obj)

            # add missing externalizations
            add_meta_items(cur, rows)
            num += len(rows)

    print(f"added {num} meta items")

    return cur


def check_transition(cur, old_code, new_code):
    oc = (old_code,)
    ds = cur.execute(f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", oc).fetchone()[0]

    items = get_items_by_dataset(cur, ds)

    tags_need_update = []

    now = get_millis()
    for g in items:
        dts_old = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ?;", (g["id"], old_code)
        ).fetchall()
        dts_new = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ?;", (g["id"], new_code)
        ).fetchall()

        if len(dts_old) > 0 and len(dts_new) == 0:
            rows = []
            for d in dts_old:
                obj = dict(d)

                tag_assig = cur.execute(
                    f"SELECT * FROM {TBL_TAG_ASS} WHERE old_tag = ? AND old_code = ? AND new_code = ?;",
                    (obj["tag_id"], old_code, new_code),
                ).fetchone()
                if not tag_assig:
                    tag_old = cur.execute(
                        f"SELECT * FROM {TBL_TAGS} WHERE id = ? AND code_id = ?;",
                        (obj["tag_id"], old_code),
                    ).fetchone()
                    # create tag and assignment
                    tag_new_id = add_tag_return_tag(
                        cur,
                        {
                            "name": tag_old["name"],
                            "description": tag_old["description"],
                            "code_id": new_code,
                            "parent": None,
                            "is_leaf": tag_old["is_leaf"],
                            "created": tag_old["created"],
                            "created_by": tag_old["created_by"],
                        },
                    )
                    add_tag_assignments(
                        cur,
                        [
                            {
                                "old_code": old_code,
                                "new_code": new_code,
                                "old_tag": tag_old["id"],
                                "new_tag": tag_new_id,
                                "description": "",
                                "created": now,
                            }
                        ],
                    )
                    tags_need_update.append((tag_old["id"], tag_new_id))
                else:
                    tag_new_id = tag_assig["new_tag"]

                del obj["id"]
                obj["tag_id"] = tag_new_id
                obj["code_id"] = new_code
                rows.append(d)

            add_datatags(cur, rows)

        # TODO: do the same for evidence

    # update parent field for newly created tags
    for old_tag, new_tag in tags_need_update:

        tag_old = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?;", (old_tag,)).fetchone()
        # get parent for old tag
        p_old = tag_old["parent"]
        if p_old:
            # get assignment for old tag's parent
            assign = cur.execute(
                f"SELECT * FROM {TBL_TAG_ASS} WHERE old_tag = ? AND old_code = ? AND new_code = ?;",
                (p_old, old_code, new_code),
            ).fetchone()
            # find matching parent for new tag
            tag_new = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?;", (new_tag,)).fetchone()
            obj = dict(tag_new)
            obj["parent"] = assign["new_tag"]
            # update new tag
            update_tags(cur, [obj])

    return cur


def get_meta_groups_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT g.* FROM {TBL_META_GROUPS} g LEFT JOIN {TBL_CODES} c ON c.id = g.code_id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def get_meta_groups_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_META_GROUPS} WHERE code_id = ?;", (code,)).fetchall()


def add_meta_groups(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    counts = {}
    datasets = set()

    for d in data:
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()
        if ds is None:
            continue

        datasets.add(ds[0])

        if "name" not in d:
            existing = cur.execute(
                f"SELECT 1 FROM {TBL_META_GROUPS} WHERE item_id = ? AND code_id = ?;",
                (d["item_id"], d["code_id"]),
            ).fetchall()
            extra = counts[d["item_id"]] if d["item_id"] in counts else 0
            d["name"] = "group " + str(len(existing) + extra + 1)
            counts[d["item_id"]] = extra + 1

        if "description" not in d:
            d["description"] = None

        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)
                ).fetchone()[0],
                d["name"],
                d["description"],
                cur.execute(
                    f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)
                ).fetchone()[0],
            ]
        )

    cur.executemany(
        f"INSERT INTO {TBL_META_GROUPS} (name, item_id, code_id, name, description, created, created_by) "
        + "VALUES (:name, :item_id, :code_id, :name, :description, :created, :created_by);",
        data,
    )

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "add meta groups", {"data": log_data})


def update_meta_groups(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:
        log_data.append(
            [
                cur.execute(
                    f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)
                ).fetchone()[0],
                d["name"],
                cur.execute(
                    f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)
                ).fetchone()[0],
            ]
        )

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()
        if ds is None:
            continue

        datasets.add(ds[0])

    cur.executemany(
        f"UPDATE {TBL_META_GROUPS} SET name = ? WHERE id = ?;",
        [(d["name"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "update meta groups", {"data": log_data})


def add_meta_group_return_id(cur, d):
    log_data = [
        cur.execute(f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)).fetchone()[0],
        cur.execute(f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)).fetchone()[
            0
        ],
    ]

    if "name" not in d:
        existing = cur.execute(
            f"SELECT id FROM {TBL_META_GROUPS} WHERE item_id = ? AND code_id = ?;",
            (d["item_id"], d["code_id"]),
        ).fetchall()
        d["name"] = "group " + str(len(existing) + 1)

    cur.execute(
        f"INSERT INTO {TBL_META_GROUPS} (name, item_id, code_id, created, created_by) "
        + "VALUES (:name, :item_id, :code_id, :created, :created_by) RETURNING id;",
        d,
    )
    id = next(cur)[0]
    ds = cur.execute(
        f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
    ).fetchone()[0]

    log_update(cur, TBL_META_GROUPS, ds)
    log_action(cur, "add meta groups", {"data": [log_data]})

    return id


def delete_meta_groups(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,),
        ).fetchone()
        if ds is not None:
            datasets.add(ds[0])

    cur.executemany(f"DELETE FROM {TBL_META_GROUPS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "delete meta groups", {"count": len(data)})


def get_meta_items_by_code(cur, code):
    return cur.execute(
        f"SELECT e.* FROM {TBL_META_ITEMS} e LEFT JOIN {TBL_META_GROUPS} eg ON e.group_id = eg.id WHERE eg.code_id = ?;",
        (code,),
    ).fetchall()


def get_meta_items_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT e.* FROM {TBL_META_ITEMS} e LEFT JOIN {TBL_META_GROUPS} eg ON e.group_id = eg.id LEFT JOIN {TBL_CODES} c ON eg.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_item_return_id(cur, d):
    if "group_id" not in d or d["group_id"] is None:
        d["group_id"] = add_meta_group_return_id(cur, d)

    if "cluster" not in d or d["cluster"] is None:
        d["cluster"] = "misc"

    ds = cur.execute(
        f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
        (d["group_id"],),
    ).fetchone()
    if ds is None:
        return None

    res = cur.execute(
        f"INSERT INTO {TBL_META_ITEMS} (group_id, name, cluster, description, created, created_by) VALUES (?,?,?,?,?,?) RETURNING id;",
        (d["group_id"], d["name"], d["cluster"], d["description"], d["created"], d["created_by"]),
    ).fetchone()
    id = res["id"] if isinstance(res, dict) else res[0]

    if "categories" in d:
        for c in d["categories"]:
            c["meta_id"] = id
        add_meta_cat_conns(cur, d["categories"])
    if "tags" in d:
        for t in d["tags"]:
            t["meta_id"] = id
        add_meta_tag_conns(cur, d["tags"])
    if "evidence" in d:
        for t in d["evidence"]:
            t["meta_id"] = id
        add_meta_ev_conns(cur, d["evidence"])

    return id


def add_meta_items(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:

        if "group_id" not in d or d["group_id"] is None:
            d["group_id"] = add_meta_group_return_id(cur, d)

        if "cluster" not in d or d["cluster"] is None:
            d["cluster"] = "misc"

        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (d["group_id"],),
        ).fetchone()
        if ds is None:
            continue

        datasets.add(ds[0])

        log_data.append([d["group_id"], d["name"], d["description"], d["cluster"]])

        add_meta_item_return_id(cur, d)

    for d in datasets:
        log_update(cur, TBL_META_ITEMS, d)

    return log_action(cur, "add meta items", {"data": log_data})


def update_meta_items(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:

        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (d["group_id"],),
        ).fetchone()
        if ds is None:
            continue

        datasets.add(ds[0])

        if "name" in d and "description" in d and "cluster" in d:

            old_group = cur.execute(
                f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d["id"],)
            ).fetchone()[0]

            cur.execute(
                f"UPDATE {TBL_META_ITEMS} SET group_id = ?, name = ?, cluster = ?, description = ? WHERE id = ?;",
                (d["group_id"], d["name"], d["cluster"], d["description"], d["id"]),
            )

            log_data.append(
                [
                    cur.execute(
                        f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (d["item_id"],)
                    ).fetchone()[0],
                    d["name"],
                    d["cluster"],
                    cur.execute(
                        f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)
                    ).fetchone()[0],
                ]
            )

            # check if old group is empty, if yes: delete it
            if old_group != d["group_id"]:
                exists = cur.execute(
                    f"SELECT 1 FROM {TBL_META_ITEMS} WHERE group_id = ?;", (old_group,)
                ).fetchone()
                if exists is None:
                    delete_meta_groups(cur, [old_group])

        if "categories" in d:
            set1 = set()
            cat_ids = cur.execute(
                f"SELECT cat_id, id FROM {TBL_META_CON_CAT} WHERE meta_id = ?;", (d["id"],)
            ).fetchall()
            for id in cat_ids:
                set1.add(id[0])

            set2 = set()
            for c in d["categories"]:
                set2.add(c["cat_id"])

            diff1 = set1.difference(set2)
            diff2 = set2.difference(set1)

            to_remove = []
            # delete old categories no longer used
            for cid, id in cat_ids:
                if cid in diff1:
                    to_remove.append(id)

            delete_meta_cat_conns(cur, to_remove)

            to_add = []
            # add new categories not previously used
            for c in d["categories"]:
                if c["cat_id"] in diff2:
                    c["meta_id"] = d["id"]
                    to_add.append(c)

            add_meta_cat_conns(cur, to_add)

        if "tags" in d:
            set1 = set()
            tag_ids = cur.execute(
                f"SELECT tag_id, id FROM {TBL_META_CON_TAG} WHERE meta_id = ?;", (d["id"],)
            ).fetchall()
            for id in tag_ids:
                set1.add(id[0])

            set2 = set()
            for t in d["tags"]:
                set2.add(t["tag_id"])

            diff1 = set1.difference(set2)
            diff2 = set2.difference(set1)

            to_remove = []
            # delete old tags no longer used
            for tid, id in tag_ids:
                if tid in diff1:
                    to_remove.append(id)

            delete_meta_tag_conns(cur, to_remove)

            to_add = []
            # add new tags not previously used
            for t in d["tags"]:
                if t["tag_id"] in diff2:
                    t["meta_id"] = d["id"]
                    to_add.append(t)

            add_meta_tag_conns(cur, to_add)

        if "evidence" in d:
            set1 = set()
            ev_ids = cur.execute(
                f"SELECT ev_id, id FROM {TBL_META_CON_EV} WHERE meta_id = ?;", (d["id"],)
            ).fetchall()
            for id in ev_ids:
                set1.add(id[0])

            set2 = set()
            for e in d["evidence"]:
                set2.add(e["ev_id"])

            diff1 = set1.difference(set2)
            diff2 = set2.difference(set1)

            to_remove = []
            # delete old evidence no longer used
            for eid, id in ev_ids:
                if eid in diff1:
                    to_remove.append(id)

            delete_meta_ev_conns(cur, to_remove)

            to_add = []
            # add new tags not previously used
            for e in d["evidence"]:
                if e["ev_id"] in diff2:
                    e["meta_id"] = d["id"]
                    to_add.append(e)

            add_meta_ev_conns(cur, to_add)

    for d in datasets:
        log_update(cur, TBL_META_ITEMS, d)

    return log_action(cur, "update meta items", {"data": log_data})


def delete_meta_items(cur, data):
    if len(data) == 0:
        return cur

    groups = set()
    datasets = set()

    for d in data:
        group_id = cur.execute(
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d,)
        ).fetchone()[0]
        groups.add(group_id)

    for id in groups:
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_ITEMS} WHERE id = ?;", [(id,) for id in data])
    for d in datasets:
        log_update(cur, TBL_META_ITEMS, d)

    log_action(cur, "delete meta items", {"count": len(data)})

    cur.executemany(f"DELETE FROM {TBL_META_CON_CAT} WHERE meta_id = ?;", [(id,) for id in data])
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_CAT, d)
        log_action(cur, "delete meta cat connections", {"count": cur.rowcount})

    cur.executemany(f"DELETE FROM {TBL_META_CON_TAG} WHERE meta_id = ?;", [(id,) for id in data])
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_TAG, d)
        log_action(cur, "delete meta tag connections", {"count": cur.rowcount})

    cur.executemany(f"DELETE FROM {TBL_META_CON_EV} WHERE meta_id = ?;", [(id,) for id in data])
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_EV, d)
        log_action(cur, "delete meta evidence connections", {"count": cur.rowcount})

    to_del = []
    for id in groups:
        res = cur.execute(f"SELECT id FROM {TBL_META_ITEMS} WHERE group_id = ?;", (id,)).fetchone()
        if res is None:
            to_del.append(id)

    return delete_meta_groups(cur, to_del)


def get_meta_categories_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_META_CATS} WHERE code_id = ?;", (code,)).fetchall()


def get_meta_categories_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT m.* FROM {TBL_META_CATS} m LEFT JOIN {TBL_CODES} c ON m.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_categories(cur, dataset, code, data):
    if len(data) == 0:
        return cur

    vals = []
    for d in data:
        if "parent" not in d:
            d["parent"] = None

        vals.append(
            (
                d["name"],
                d["description"],
                d["parent"],
                d["created"],
                d["created_by"],
                dataset,
                code,
            )
        )

    cur.executemany(
        f"INSERT INTO {TBL_META_CATS} (name, description, parent, created, created_by, dataset_id, code_id) VALUES (?, ?, ?, ?, ?, ?, ?);",
        vals,
    )

    log_update(cur, TBL_META_CATS, dataset)
    return log_action(
        cur, "add meta categories", {"names": [d["name"] for d in data]}, data[0]["created_by"]
    )


def add_meta_category_return_id(cur, data):
    cat = cur.execute(
        f"INSERT INTO {TBL_META_CATS} (name, description, parent, created, created_by, dataset_id, code_id) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id;",
        (
            data["name"],
            data["description"],
            data["parent"],
            data["created"],
            data["created_by"],
            data["dataset_id"],
            data["code_id"],
        ),
    ).fetchone()
    user_name = cur.execute(
        f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (data["created_by"],)
    ).fetchone()[0]
    log_update(cur, TBL_META_CATS, data["dataset_id"])
    log_action(
        cur, "add meta categories", {"name": data["name"], "user": user_name}, data["created_by"]
    )
    return cat[0]


def update_meta_categories(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        if "parent" not in d:
            d["parent"] = None

        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],)
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(
        f"UPDATE {TBL_META_CATS} SET name = :name, description = :description, parent = :parent WHERE id = :id;",
        data,
    )

    for d in datasets:
        log_update(cur, TBL_META_CATS, d)

    return log_action(cur, "update meta categories", {"names": [d["name"] for d in data]})


def delete_meta_categories(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_CATS} m ON c.id = m.code_id WHERE m.id = ?;",
            (id,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_CATS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_CATS, d)

    return log_action(cur, "delete meta categories", {"count": len(data)})


def get_meta_cat_conns_by_code(cur, code):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_CAT} a LEFT JOIN {TBL_META_CATS} b ON a.cat_id = b.id WHERE b.code_id = ?;",
        (code,),
    ).fetchall()


def get_meta_cat_conns_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_CAT} a LEFT JOIN {TBL_META_CATS} b ON a.cat_id = b.id "
        + f"LEFT JOIN {TBL_CODES} c ON b.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_cat_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        group = cur.execute(
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d["meta_id"],)
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(
        f"INSERT INTO {TBL_META_CON_CAT} (meta_id, cat_id) VALUES (?, ?);",
        [(d["meta_id"], d["cat_id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_META_CON_CAT, d)

    return log_action(cur, "add meta cat connections", {"count": len(data)})


def delete_meta_cat_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        group = cur.execute(
            f"SELECT i.group_id FROM {TBL_META_ITEMS} i LEFT JOIN {TBL_META_CON_CAT} c ON c.meta_id = i.id WHERE c.id = ?;",
            (id,),
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_CON_CAT} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_CON_CAT, d)

    return log_action(cur, "delete meta cat connections", {"count": len(data)})


def get_meta_tag_conns_by_code(cur, code):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_TAG} a LEFT JOIN {TBL_TAGS} b ON a.tag_id = b.id WHERE b.code_id = ?;",
        (code,),
    ).fetchall()


def get_meta_tag_conns_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_TAG} a LEFT JOIN {TBL_TAGS} b ON a.tag_id = b.id "
        + f"LEFT JOIN {TBL_CODES} c ON b.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_tag_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        group = cur.execute(
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d["meta_id"],)
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(
        f"INSERT INTO {TBL_META_CON_TAG} (meta_id, tag_id) VALUES (?, ?);",
        [(d["meta_id"], d["tag_id"]) for d in data],
    )
    for d in datasets:
        log_update(cur, TBL_META_CON_TAG, d)

    return log_action(cur, "add meta tag connections", {"count": len(data)})


def delete_meta_tag_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        group = cur.execute(
            f"SELECT i.group_id FROM {TBL_META_ITEMS} i LEFT JOIN {TBL_META_CON_TAG} c ON c.meta_id = i.id WHERE c.id = ?;",
            (id,),
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_CON_TAG} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_CON_TAG, d)

    return log_action(cur, "delete meta tag connections", {"count": len(data)})


def get_meta_ev_conns_by_code(cur, code):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_EV} a LEFT JOIN {TBL_EVIDENCE} b ON a.ev_id = b.id WHERE b.code_id = ?;",
        (code,),
    ).fetchall()


def get_meta_ev_conns_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_CON_EV} a LEFT JOIN {TBL_EVIDENCE} b ON a.ev_id = b.id "
        + f"LEFT JOIN {TBL_CODES} c ON b.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_ev_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        group = cur.execute(
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d["meta_id"],)
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(
        f"INSERT INTO {TBL_META_CON_EV} (meta_id, ev_id) VALUES (?, ?);",
        [(d["meta_id"], d["ev_id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_META_CON_EV, d)

    return log_action(cur, "add meta evidence connections", {"count": len(data)})


def delete_meta_ev_conns(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        group = cur.execute(
            f"SELECT i.group_id FROM {TBL_META_ITEMS} i LEFT JOIN {TBL_META_CON_EV} c ON c.meta_id = i.id WHERE c.id = ?;",
            (id,),
        ).fetchone()[0]
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_CON_EV} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_CON_EV, d)

    return log_action(cur, "delete meta evidence connections", {"count": len(data)})


def get_meta_agreements_by_code(cur, code):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_AG} a "
        + f"LEFT JOIN {TBL_META_ITEMS} b ON a.meta_id = b.id "
        + f"LEFT JOIN {TBL_META_GROUPS} c ON b.group_id = c.id WHERE c.code_id = ?;",
        (code,),
    ).fetchall()


def get_meta_agreements_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT a.* FROM {TBL_META_AG} a "
        + f"LEFT JOIN {TBL_META_ITEMS} b ON a.meta_id = b.id "
        + f"LEFT JOIN {TBL_META_GROUPS} c ON b.group_id = c.id "
        + f"LEFT JOIN {TBL_CODES} d ON c.code_id = d.id WHERE d.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_agreements(cur, data):
    if len(data) == 0:
        return cur

    log_data = []
    datasets = set()

    for d in data:

        (meta_name,) = cur.execute(
            f"SELECT name FROM {TBL_META_ITEMS} WHERE id = ?;", (d["meta_id"],)
        ).fetchone()

        if "item_id" not in d:
            (item_id,) = cur.execute(
                f"SELECT a.item_id FROM {TBL_META_GROUPS} a "
                + f"LEFT JOIN {TBL_META_ITEMS} b ON a.id = b.group_id WHERE b.id = ?;",
                (d["meta_id"],),
            ).fetchone()
        else:
            item_id = d["item_id"]

        datasets.add(
            cur.execute(
                f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id = ?;", (item_id,)
            ).fetchone()[0]
        )

        item_name = cur.execute(
            f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;", (item_id,)
        ).fetchone()[0]
        user_name = cur.execute(
            f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (d["created_by"],)
        ).fetchone()[0]
        log_data.append([item_name, meta_name, user_name, d["value"]])

    cur.executemany(
        f"INSERT INTO {TBL_META_AG} (meta_id, created_by, value) VALUES (:meta_id, :created_by, :value);",
        data,
    )
    for d in datasets:
        log_update(cur, TBL_META_AG, d)

    return log_action(cur, "add meta agreements", {"data": log_data})


def update_meta_agreements(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        group = cur.execute(
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;", (d["meta_id"],)
        ).fetchone()
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} g ON c.id = g.code_id WHERE g.id = ?;",
            group,
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(
        f"UPDATE {TBL_META_AG} SET value = ? WHERE id = ?;", [(d["value"], d["id"]) for d in data]
    )
    for d in datasets:
        log_update(cur, TBL_META_AG, d)

    return log_action(cur, "update meta agreements", {"count": len(data)})


def delete_meta_agreements(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for id in data:
        group = cur.execute(
            f"SELECT i.group_id FROM {TBL_META_ITEMS} i LEFT JOIN {TBL_META_AG} ag ON ag.meta_id = i.id WHERE ag.id = ?;",
            (id,),
        ).fetchone()
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} g ON c.id = g.code_id WHERE g.id = ?;",
            group,
        ).fetchone()[0]
        datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_META_AG} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_AG, d)

    return log_action(cur, "delete meta agreements", {"count": len(data)})
