import json
from collections import namedtuple
from datetime import datetime, timezone
from shutil import rmtree
from argon2 import PasswordHasher

from table_constants import (
    TBL_CODES,
    TBL_DATASETS,
    TBL_DATATAGS,
    TBL_EVIDENCE,
    TBL_EXPERTISE,
    TBL_ITEMS,
    TBL_ITEMS_FINAL,
    TBL_LOGS,
    TBL_META_AG,
    TBL_META_CATS,
    TBL_META_CON_CAT,
    TBL_META_CON_EV,
    TBL_META_CON_TAG,
    TBL_META_GROUPS,
    TBL_META_ITEMS,
    TBL_OBJECT,
    TBL_PRJ_USERS,
    TBL_SCORES,
    TBL_SCORES_ITEMS,
    TBL_SCORES_TAGS,
    TBL_TAG_ASS,
    TBL_TAGS,
    TBL_TRANS,
    TBL_UPDATES,
    TBL_USERS,
    TBL_USER_SESS
)

USER_ROLES = ["guest", "collaborator", "admin"]
USER_ROLE_DEFAULT = USER_ROLES[1]

OBJ_STATUS_OPEN = 1
OBJ_STATUS_CLOSED_APPROVE = 2
OBJ_STATUS_CLOSED_DENY = 3

def namedtuple_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    cls = namedtuple("Row", fields)
    return cls._make(row)


def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def get_millis():
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def parse(d, name):
    if isinstance(d, dict):
        return d.get(name, None)

    return getattr(d, name, None)


def one_or_none(cur, stmt, data, attr=None):
    res = cur.execute(stmt, data).fetchone() if data is not None else None
    if res is None:
        return None

    if attr is not None:
        return parse(res, attr)

    return res if isinstance(res, dict) else res[0]


def log_update(cur, name, dataset):
    return cur.execute(
        f"INSERT OR REPLACE INTO {TBL_UPDATES} (name, dataset_id, timestamp) VALUES (?,?,?);",
        (name, dataset, get_millis())
    )


def log_action(cur, action, data=None, user=None):
    if user is None or data is None or (isinstance(data, list) and len(data) == 0):
        return cur
    return cur.execute(
        f"INSERT INTO {TBL_LOGS} (user_id, timestamp, action, data) VALUES (?,?,?,?)",
        (user, get_millis(), action, json.dumps(data)),
    )


def make_space(length):
    return ",".join(["?"] * length)


def session_id_exists(cur, id):
    return one_or_none(
        cur,
        f"SELECT id FROM {TBL_USER_SESS} WHERE session_id = ?;",
        (id,)
    ) is not None


def get_meta_table(cur, dataset):
    res = cur.execute(
        f"SELECT meta_table FROM {TBL_DATASETS} WHERE id = ?;", (dataset,)
    ).fetchone()
    return parse(res, "meta_table")


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
        if it:
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
    if ds["schema"]:
        ds["schema"] = json.loads(ds["schema"] if isinstance(ds["schema"], str) else ds["schema"].decode("utf-8"))
    return ds


def get_dataset_id_by_code(cur, code):
    return one_or_none(
        cur,
        f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;",
        (code,),
        "dataset_id"
    )


def get_dataset_id_by_item(cur, item):
    return one_or_none(
        cur,
        f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id = ?;",
        (item,),
        "dataset_id"
    )


def get_dataset_id_by_tag(cur, tag):
    return one_or_none(
        cur,
        f"""SELECT c.dataset_id FROM {TBL_CODES} c
            LEFT JOIN {TBL_TAGS} t ON c.id = t.code_id
            WHERE t.id = ?;""",
        (tag,),
        "dataset_id"
    )


def get_datasets(cur):
    datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS}").fetchall()
    for ds in datasets:
        del ds["meta_table"]
        if ds["schema"]:
            ds["schema"] = json.loads(ds["schema"] if isinstance(ds["schema"], str) else ds["schema"].decode("utf-8"))
        ds["users"] = [u["id"] for u in get_users_by_dataset(cur, ds["id"])]

    return datasets

def get_datasets_by_user(cur, uid):
    ids = cur.execute(f"SELECT dataset_id FROM {TBL_PRJ_USERS} WHERE user_id = ?;", (uid,)).fetchall()
    return [parse(id, "dataset_id") for id in ids if id is not None]

def add_dataset_return_id(cur, obj, loguser=None):

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

    if "schema" in obj and "columns" in obj["schema"] and len(obj["schema"]["columns"]) > 0:

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
    log_action(cur, "add dataset", obj, loguser)

    return id


def add_datasets(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    ids = []
    for d in data:
        try:
            ids.append(add_dataset_return_id(cur, d, loguser))
        except ValueError as e:
            print(f"could not add dataset {d['name']}")

    return ids


def update_datasets(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    for d in data:

        if "id" not in d:
            raise ValueError("missing dataset field: id")
        if "name" not in d:
            raise ValueError("missing dataset field: name")
        if "description" not in d:
            raise ValueError("missing dataset field: description")

        cur.execute(
            f"UPDATE {TBL_DATASETS} SET name = ?, description = ? WHERE id = ?;",
            (d["name"], d["description"], d["id"])
        )

        if "users" in d:
            existing = [u.id for u in get_users_by_dataset(cur, d["id"])]
            toadd = [u for u in d["users"] if u not in existing]
            todel = [u for u in existing if u not in d["users"]]

            if len(toadd) > 0:
                add_users_to_project(cur, d["id"], toadd, loguser)

            if len(todel) > 0:
                delete_users_from_project(cur, d["id"], todel, loguser)

        log_update(cur, TBL_DATASETS, d["id"])

    log_action(cur, "updated datasets", [{ "id": d["id"], "name": d["name"] } for d in data], loguser)

    return cur


def delete_datasets(cur, ids, teaser_path, evidence_path, loguser=None):
    if len(ids) == 0:
        return cur

    logdata = []

    for id in ids:
        dst = cur.execute(f"SELECT meta_table FROM {TBL_DATASETS} WHERE id = ?;", (id,)).fetchone()
        tbl = None
        if dst is not None:
            tbl = parse(dst, "meta_table")

        # delete table
        if tbl is not None:
            cur.execute(f"DELETE FROM {tbl};")
            cur.execute(f"DROP TABLE {tbl};")
            print("dropped table", tbl)


        codes = cur.execute(
            f"SELECT id from {TBL_CODES} WHERE dataset_id = ? ORDER BY id;", (id,)
        ).fetchall()
        # delete codes (just making sure)
        cur.execute(f"DELETE FROM {TBL_CODES} WHERE dataset_id = ?;", (id,))
        print("\tdeleted codes")

        # delete items
        cur.execute(f"DELETE FROM {TBL_ITEMS} WHERE dataset_id = ?;", (id,))
        print("\tdeleted items", id)

        # delete tags
        cur.execute(
            f"DELETE FROM {TBL_TAGS} WHERE code_id in ({make_space(len(codes))});",
            [c[0] for c in codes]
        )

        # delete project users
        cur.execute(f"DELETE FROM {TBL_PRJ_USERS} WHERE dataset_id = ?;", (id,))
        print("\tdeleted project users")

        dsname = cur.execute(f"SELECT name FROM {TBL_DATASETS} WHERE id = ?;", (id,)).fetchone()
        logdata.append({ "id": id, "name": dsname[0] })

        cur.execute(f"DELETE FROM {TBL_DATASETS} WHERE id = ?;", (id,))
        print("\tdeleted dataset", id)

        # delete media (teaser)
        tp = teaser_path.joinpath(str(id))
        if tp.exists():
            rmtree(tp)
            print("\tdeleted teasers")

        # delete media (evidence)
        ep = evidence_path.joinpath(str(id))
        if ep.exists():
            rmtree(ep)
            print("\tdeleted evidence")

    for id in ids:
        log_update(cur, TBL_DATASETS, id)

    log_action(cur, "deleted datasets", logdata, loguser)

    return cur


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
        (dataset,)
    ).fetchall()

def get_items_by_code(cur, code):
    dataset = get_dataset_id_by_code(cur, code)
    codes = get_code_ids_before(cur, dataset, code)

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
        f"""SELECT i.*, {columns} FROM {TBL_ITEMS} i
            LEFT JOIN {tbl_name} g ON i.id = g.item_id
            WHERE i.code_id IN ({make_space(len(codes))}) ORDER BY i.id;""",
        codes
    ).fetchall()

def get_items_merged_by_code(cur, code):
    items = get_items_by_code(cur, code)

    for d in items:
        d["tags"] = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ?;", (d["id"], code)
        ).fetchall()

    return items


def get_items_finalized_by_code(cur, code):
    dataset = get_dataset_id_by_code(cur, code)
    codes = get_code_ids_before(cur, dataset, code)
    return cur.execute(
        f"SELECT f.* FROM {TBL_ITEMS_FINAL} f LEFT JOIN {TBL_ITEMS} i ON i.id = f.item_id "+
        f"WHERE i.code_id IN ({make_space(len(codes))}) ORDER BY f.item_id;",
        codes
    ).fetchall()


def get_items_finalized_by_user(cur, user_id):
    return cur.execute(
        f"SELECT * FROM {TBL_ITEMS_FINAL} WHERE user_id = ? ORDER BY item_id;",
        (user_id,)
    ).fetchall()


def add_item_return_id(cur, d, loguser=None):

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

    if "description" not in d:
        d["description"] = None
    if "url" not in d:
        d["url"] = None
    if "teaser" not in d:
        d["teaser"] = None
    if "created" not in d:
        d["created"] = get_millis()

    res = cur.execute(
        f"INSERT INTO {TBL_ITEMS} (dataset_id, code_id, created, created_by, name, description, url, teaser) VALUES (?, ?, ?, ?, ?) RETURNING id;",
        (dataset, d["code_id"], d["created"], d["created_by"], d["name"], d["description"], d["url"], d["teaser"]),
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
    log_action(cur, "add item", { "id": d["item_id"], "name": d["name"] }, loguser)

    return d["item_id"]

def add_items(cur, dataset, code, data, loguser=None):
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

    ids = {}
    names = {}
    now = get_millis()

    for i, d in enumerate(data):
        if "description" not in d:
            d["description"] = None
        if "url" not in d:
            d["url"] = None
        if "teaser" not in d:
            d["teaser"] = None
        if "created" not in d:
            d["created"] = now

        if "id" in d:
            cur.execute(
                f"INSERT INTO {TBL_ITEMS} (id, dataset_id, code_id, created, created_by, name, description, url, teaser) VALUES (?,?,?,?,?,?,?,?,?);",
                (d["id"], dataset, code, d["created"], d["created_by"], d["name"], d["description"], d["url"], d["teaser"]),
            )
            d["item_id"] = d["id"]
        else:
            res = cur.execute(
                f"INSERT INTO {TBL_ITEMS} (dataset_id, code_id, created, created_by, name, description, url, teaser) VALUES (?,?,?,?,?,?,?,?) RETURNING id;",
                (dataset, code, d["created"], d["created_by"], d["name"], d["description"], d["url"], d["teaser"]),
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

        ids[i] = d["item_id"]
        names[i] = d["name"]

    log_update(cur, TBL_ITEMS, dataset)
    log_action(cur, "add items", [{ "id": id, "name": names[idx] } for idx, id in ids.items()], loguser)

    return ids


def update_items(cur, data, loguser=None):
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

    return log_action(
        cur,
        "update items",
        [{ "id": d["id"], "name": d["name"] } for d in data],
        loguser
    )


def finalize_items(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    now = get_millis()
    cleaned = []
    logdata = []
    ds = set()

    for d in data:
        d["timestamp"] = now
        if "user_id" in d and "item_id" in d:
            dsid = get_dataset_id_by_item(cur, d["item_id"])
            if dsid is None:
                continue

            ds.add(dsid)
            cleaned.append(d)

            item_name = one_or_none(cur,
                f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
                (d["item_id"],)
            )
            logdata.append({
                "user_id": d["user_id"],
                "item": { "id": d["item_id"], "name": item_name }
            })

    cur.executemany(
        f"INSERT OR IGNORE INTO {TBL_ITEMS_FINAL} (item_id, user_id, timestamp) " +
        "VALUES (:item_id, :user_id, :timestamp)",
        cleaned
    )

    for d in ds:
        log_update(cur, TBL_ITEMS_FINAL, d)

    return log_action(cur, "finalized items", logdata, loguser)


def delete_items(cur, data, base_path, loguser=None):
    if len(data) == 0:
        return cur

    ds = cur.execute(
        f"SELECT dataset_id FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchone()[0]
    logdata = cur.execute(
        f"SELECT id, name FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchall()
    filenames = cur.execute(
        f"SELECT teaser FROM {TBL_ITEMS} WHERE id IN ({make_space(len(data))});", data
    ).fetchall()

    cur.executemany(f"DELETE FROM {TBL_ITEMS} WHERE id = ?;", [(id,) for id in data])

    tbl_name = get_meta_table(cur, ds)
    cur.executemany(f"DELETE FROM {tbl_name} WHERE item_id = ?;", [(id,) for id in data])

    log_update(cur, TBL_ITEMS, ds)
    log_action(cur, "delete items", [{ "id": n[0], "name": n[1] } for n in logdata], loguser)

    dspath = str(ds)

    for f in filenames:
        if f[0] is not None:
            base_path.joinpath(dspath, f[0]).unlink(missing_ok=True)

    return cur


def get_item_expertise_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT ge.* FROM {TBL_EXPERTISE} ge LEFT JOIN {TBL_ITEMS} g ON ge.item_id = g.id WHERE g.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_item_expertise(cur, data, loguser=None):
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
        cur.executemany(
            f"INSERT INTO {TBL_EXPERTISE} (item_id, user_id, value) VALUES (:item_id, :user_id, :value);",
            newones,
        )
        log_update(cur, TBL_EXPERTISE, ds[0])
        log_action(
            cur,
            "add expertise",
            [
                {
                    "item_id": newones[i]["item_id"],
                    "user_id": newones[i]["user_id"],
                    "value": newones[i]["value"]
                } for i in range(len(newones))
            ],
            loguser
        )

    if len(existing) > 0:
        update_item_expertise(cur, existing)

    return cur


def update_item_expertise(cur, data, loguser=None):
    if len(data) == 0:
        return cur

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
        [
            {
                "item_id": data[i]["item_id"],
                "user_id": data[i]["user_id"],
                "value": data[i]["value"]
            } for i in range(len(data))
        ],
        loguser
    )


def delete_item_expertise(cur, ids, loguser=None):
    if len(ids) == 0:
        return cur

    logdata = []
    for id in ids:
        exp = cur.execute(
            f"SELECT (item_id, user_id) FROM {TBL_EXPERTISE} WHERE id = ?;",
            (id,)
        ).fetchone()

        if exp is not None:
            logdata.append({ "item_id": exp[0], "user_id": exp[1] })

    ds = cur.execute(
        f"SELECT i.dataset_id FROM {TBL_ITEMS} i LEFT JOIN {TBL_EXPERTISE} e ON i.id = e.item_id WHERE e.id = ?;",
        (ids[0],)
    ).fetchone()

    cur.executemany(f"DELETE FROM {TBL_EXPERTISE} WHERE id = ?;", [(id,) for id in ids])

    log_update(cur, TBL_EXPERTISE, ds[0])
    return log_action(cur, "delete expertise", logdata, loguser)

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
    users = cur.execute(f"SELECT id, name, role, email from {TBL_USERS};").fetchall()
    for u in users:
        u["projects"] = get_datasets_by_user(cur, u["id"])
    return users

def add_user_return_id(cur, d, loguser=None):
    if "name" not in d:
        return None

    ph = PasswordHasher()
    if "role" not in d or d["role"] is None or len(d["role"]) == 0 or d["role"] not in USER_ROLES:
        d["role"] = USER_ROLE_DEFAULT
    if "email" not in d or d["email"] is None or len(d["email"]) == 0:
        d["email"] = None

    if "pw_hash" not in d:
        if "password" in d and len(d["password"]) > 0:
            d["pw_hash"] = ph.hash(d["password"])
        else:
            d["pw_hash"] = ph.hash(d["name"])

    res = cur.execute(
        f"INSERT INTO {TBL_USERS} (name, role, email, pw_hash) VALUES (?,?,?,?) RETURNING id;",
        (d["name"], d["role"], d["email"], d["pw_hash"])
    ).fetchone()

    log_action(cur, "add user", { "name": d["name"], "role": d["role"] }, loguser)
    return parse(res, "id")


def add_users(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    ids = []
    ds = set()

    for d in data:
        if "name" not in d:
            continue

        uid = add_user_return_id(cur, d, loguser)
        if uid is None:
            continue

        ids.append(uid)
        obj = { "id": uid, "name": d["name"], "role": d["role"], "datasets": [] }

        if "projects" in d:
            for p in d["projects"]:
                obj["datasets"].append(p)
                add_users_to_project(cur, p, [uid], loguser)
                ds.add(p)

    for d in ds:
        log_update(cur, "project_users", d)

    return cur


def update_users(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    ds = set()

    for d in data:

        if "dataset_id" in d:
            ds.add(d["dataset_id"])

        if d["role"] not in USER_ROLES:
            d["role"] = USER_ROLE_DEFAULT

        cur.execute(
            f"UPDATE {TBL_USERS} SET name = ?, role = ?, email = ? WHERE id = ?;",
            (d["name"], d["role"], d["email"], d["id"])
        )

        if "projects" in d:
            existing = get_datasets_by_user(cur, d["id"])
            # projects the user should be added to
            toadd = [p for p in d["projects"] if p not in existing]
            # projects the user should be removed from
            todel = [p for p in existing if p not in d["projects"]]

            for p in toadd:
                ds.add(p)
                add_users_to_project(cur, p, [d["id"]], loguser)

            for p in todel:
                ds.add(p)
                delete_users_from_project(cur, p, [d["id"]], loguser)
        else:
            ids = get_datasets_by_user(cur, d["id"])
            for id in ids:
                ds.add(id)

    log_action(
        cur,
        "update users",
        [{ "id": d["id"], "name": d["name"], "role": d["role"] } for d in data],
        loguser
    )

    for d in ds:
        log_update(cur, "project_users", d)

    return cur


def delete_users(cur, ids, loguser=None):

    if len(ids) == 0:
        return cur

    ds = set()
    names = {}

    for d in ids:
        dids = get_datasets_by_user(cur, d)
        for id in dids:
            ds.add(id)
            names[id] = cur.execute(
                f"SELECT name FROM {TBL_USERS} WHERE id = ?;", (id,)
            ).fetchone()[0]

    cur.executemany(f"DELETE FROM {TBL_USERS} WHERE id = ?;", [(id,) for id in ids])

    log_action(cur, "delete users", [{ "id": id, "name": names[id] } for id in ids], loguser)
    for d in ds:
        log_update(cur, "project_users", d)

    return cur


def has_project_user_by_id(cur, dataset, id):
    return cur.execute(f"SELECT id from {TBL_PRJ_USERS} WHERE dataset_id = ? AND user_id = ?;", (dataset, id)).fetchone() is not None


def add_users_to_project(cur, dataset, user_ids, loguser=None):
    if len(user_ids) == 0:
        return cur

    cur.executemany(
        f"INSERT OR IGNORE INTO {TBL_PRJ_USERS} (user_id, dataset_id) VALUES (?, ?);",
        [(id, dataset) for id in user_ids],
    )

    log_update(cur, TBL_USERS, dataset)
    return log_action(cur, "add project users", { "dataset_id": dataset, "user_ids": user_ids }, loguser)


def delete_users_from_project(cur, dataset, user_ids, loguser=None):
    if len(user_ids) == 0:
        return cur

    cur.executemany(
        f"DELETE FROM {TBL_PRJ_USERS} WHERE user_id = ? AND dataset_id = ?;",
        [(id, dataset) for id in user_ids],
    )

    log_update(cur, TBL_USERS, dataset)
    return log_action(cur, "delete project users", { "dataset_id": dataset, "user_ids": user_ids }, loguser)


def get_codes_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT * from {TBL_CODES} WHERE dataset_id = ? ORDER BY id;",
        (dataset,)
    ).fetchall()


def get_code_ids_before(cur, dataset, code):
    codes = get_codes_by_dataset(cur, dataset)
    return [parse(c, "id") for c in codes if parse(c, "id") <= code]

def add_code_return_id(cur, dataset, d, loguser=None):
    id = cur.execute(
        f"INSERT INTO {TBL_CODES} (dataset_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?) RETURNING id;",
        (dataset, d["name"], d["description"], d["created"], d["created_by"]),
    ).fetchone()[0]

    log_update(cur, TBL_CODES, dataset)
    log_action(cur, "add codes", { "id": id, "name": d["name"], "dataset_id": dataset }, loguser)
    return id


def add_codes(cur, dataset, data, loguser=None):
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
        cur, "add codes", [{ "name": d["name"], "dataset_id": dataset } for d in data], loguser
    )


def update_codes(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    rows = []
    for d in data:
        rows.append((d["name"], d["description"], d["id"]))

    cur.executemany(f"UPDATE {TBL_CODES} SET name = ?, description = ? WHERE id = ?;", rows)

    log_update(cur, TBL_CODES, data[0]["dataset_id"])
    return log_action(
        cur, "update codes", [{ "id": d["id"], "name": d["name"] } for d in data],
        loguser
    )


def get_tags_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT t.* from {TBL_TAGS} t LEFT JOIN {TBL_CODES} c ON t.code_id = c.id WHERE c.dataset_id = ? ORDER BY t.id;",
        (dataset,)
    ).fetchall()


def get_tags_by_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_TAGS} WHERE code_id = ? ORDER BY id;", (code,)).fetchall()


def add_tag_return_id(cur, d, loguser=None):
    tag = add_tag_return_tag(cur, d, loguser)
    return tag.id


def add_tag_return_tag(cur, d, loguser=None):
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
        update_tags_is_leaf(cur, [d["parent"]], loguser)

    ds = cur.execute("SELECT dataset_id FROM codes WHERE id = ?;", (d["code_id"],)).fetchone()

    log_update(cur, TBL_TAGS, ds[0])
    log_action(cur, "add tag", { "id": tag[0], "name": d["name"], "code_id": d["code_id"] }, loguser)
    return tag


def add_tags(cur, data, loguser=None):
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

        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is not None:
            datasets.add(ds)

        if "id" in d:
            cur.execute(
                f"""INSERT INTO {TBL_TAGS} (
                    id,
                    code_id,
                    name,
                    description,
                    created,
                    created_by,
                    parent,
                    is_leaf
                ) VALUES (
                    :id,
                    :code_id,
                    :name,
                    :description,
                    :created,
                    :created_by,
                    :parent,
                    :is_leaf
                );""",
                d
            )
            ids.append(d["id"])
            log_action(
                cur,
                "add tag", {
                    "id": d["id"],
                    "name": d["name"],
                    "code_id": d["code_id"]
            }, loguser)

        else:
            tid = add_tag_return_id(cur, d, loguser)
            ids.append(tid)
            if d["parent"] is not None:
                ids.append(d["parent"])

        # get tag assignment for this tag for all transitions *from* this code
        trans = cur.execute(
            f"SELECT * FROM {TBL_TRANS} WHERE old_code = ?;", (d["code_id"],)
        ).fetchall()

        for t in trans:
            rows.append({
                "old_code": d["code_id"],
                "new_code": t.new_code,
                "old_tag": ids[-1],
                "new_tag": None,
                "description": "ADDED TAG AFTERWARDS",
                "created": now,
            })

        # get tag assignment for this tag for all transitions *to* this code
        trans = cur.execute(
            f"SELECT * FROM {TBL_TRANS} WHERE new_code = ?;", (d["code_id"],)
        ).fetchall()

        for t in trans:
            rows.append({
                "old_code": t.old_code,
                "new_code": d["code_id"],
                "old_tag": None,
                "new_tag": ids[-1],
                "description": "ADDED TAG AFTERWARDS",
                "created": now,
            })

    add_tag_assignments(cur, rows, loguser)

    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    return update_tags_is_leaf(cur, ids, loguser)


def add_tags_for_assignment(cur, data, loguser=None):
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
                    loguser
                )

    return cur


def update_tags_is_leaf(cur, ids, loguser=None):
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

        has_children = cur.execute(f"SELECT id FROM {TBL_TAGS} WHERE parent = ?;", (id,)).fetchone()
        name = one_or_none(
            cur,
            f"SELECT name FROM {TBL_TAGS} WHERE id = ?;",
            (id,),
            "name"
        )
        rows.append({ "is_leaf": 0 if has_children is not None else 1, "id": id, "name": name })

        pid = one_or_none(cur, f"SELECT parent FROM {TBL_TAGS} WHERE id = ?;", (id,))
        if pid is not None:
            pname = one_or_none(
                cur,
                f"SELECT name FROM {TBL_TAGS} WHERE id = ?;",
                (pid,),
                "name"
            )
            rows.append({ "is_leaf": 0, "id": pid, "name": pname })

    # update is_leaf for all tags that where changed
    cur.executemany(f"UPDATE {TBL_TAGS} SET is_leaf = :is_leaf WHERE id = :id;", rows)

    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    return log_action(cur, "update tags leaf status", rows, loguser)


def update_tags(cur, data, loguser=None):
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

    log_action(
        cur,
        "update tags",
        [{ "id": d["id"], "name": d["name"], "parent": d["parent"] } for d in data],
        loguser
    )
    # update is_leaf for all tags that where changed
    return update_tags_is_leaf(cur, tocheck, loguser)


def group_tags(cur, parent, data, loguser=None):
    if len(data) == 0:
        return cur

    log_action(
        cur,
        "merge tags",
        {
            "parent": { "id": parent["id"], "name": parent["name"] },
            "children": [{ "id": d["id"], "name": d["name"] } for d in data]
        },
        loguser
    )
    id = add_tag_return_id(cur, parent, loguser)

    for d in data:
        d["parent"] = id

    return update_tags(cur, data, loguser)


def split_tags(cur, data, evidence_path, loguser=None):
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

        log_action(cur, "split tag", { "id": tag.id, "name": tag.name }, loguser)

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
                loguser
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

            add_tag_assignments(cur, rows, loguser)

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
                    (c["tag_id"], e.id, d["id"]),
                )

        # update datatags
        update_datatags(cur, rows, loguser)

        if first is not None:
            rows = []
            # update parent reference
            for t in children:
                c = t._asdict()
                c["parent"] = first[0]
                rows.append(c)

            update_tags(cur, rows)

        # delete tag that is being split
        delete_tags(cur, [d["id"]], evidence_path, loguser)

        # delete old tag assignments (if still present)
        delete_tag_assignments(cur, [a.id for a in assigsOLD], loguser)
        delete_tag_assignments(cur, [a.id for a in assigsNEW], loguser)

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


def merge_tags(cur, data, evidence_path, loguser=None):
    if len(data) == 0:
        return cur

    for d in data:
        if "ids" not in d:
            continue

        tags = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE id IN ({make_space(len(d['ids']))});", d["ids"]
        ).fetchall()
        parent = d["parent"] if "parent" in d else get_highest_parent(cur, d["ids"])

        log_action(
            cur,
            "merge tags",
            [{ "id": t.id, "name": t.name } for t in tags],
            loguser
        )

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
        new_tag = add_tag_return_tag(cur, obj, loguser)

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

            add_tag_assignments(cur, rows, loguser)

            delete_tag_assignments(cur, [a.id for a in assigsOLD], loguser)
            delete_tag_assignments(cur, [a.id for a in assigsNEW], loguser)

        rows = []
        children = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE parent IN ({make_space(len(tags))});", d["ids"]
        ).fetchall()
        for t in children:
            c = t._asdict()
            c["parent"] = new_tag.id
            rows.append(c)

        # update child tags
        update_tags(cur, rows, loguser)

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
        add_datatags(cur, rows, loguser)

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
        delete_tags(cur, d["ids"], evidence_path, loguser)

        # rename new tag
        obj["name"] = d["name"]
        obj["id"] = new_tag.id
        update_tags(cur, [obj], loguser)

    return cur


def delete_tags(cur, ids, evidence_path, loguser=None):
    if len(ids) == 0:
        return cur

    tocheck = []
    datasets = set()
    logdata = []

    for id in ids:
        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,),
        ).fetchone()

        if ds is None:
            continue

        datasets.add(ds[0])

        pid = one_or_none(cur, f"SELECT parent FROM {TBL_TAGS} WHERE id = ?;", (id,))
        children = cur.execute(
            f"SELECT id, name FROM {TBL_TAGS} WHERE parent = ?;", (id,)
        ).fetchall()

        if pid is not None:
            tocheck.append(pid)

        # remove this node as parent
        cur.executemany(
            f"UPDATE {TBL_TAGS} SET parent = ? WHERE id = ?;",
            [(pid, t[0]) for t in children],
        )
        if len(children) > 0:
            log_action(
                cur,
                "update tag parent",
                [{ "id": d.id, "name": d.name } for d in children],
                loguser
            )

        # get the name of this tag
        name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?", (id,))
        logdata.append({ "id": id, "name": name })

    # remove datatags for tags
    delete_datatags_by_tags(cur, ids, loguser)

    # remove tag assignments for tags
    delete_tag_assignments_by_tag(cur, ids, loguser)

    # remove externalization connections to tags if tags are deleted
    delete_meta_tag_conns_by_tag(cur, ids, loguser)

    # delete all evidence for these tags
    delete_evidence_by_tag(cur, ids, evidence_path, loguser)

    cur.executemany(f"DELETE FROM {TBL_TAGS} WHERE id = ?;", [(id,) for id in ids])
    log_action(cur, "delete tags", logdata, loguser)

    for d in datasets:
        log_update(cur, TBL_TAGS, d)

    return update_tags_is_leaf(cur, tocheck, loguser)


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


def add_datatags(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    rows = []
    logdata = {}
    with_id = "id" in data[0]
    datasets = set()

    for d in data:
        if with_id:
            rows.append(
                (d["id"], d["item_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"])
            )
        else:
            rows.append((d["item_id"], d["tag_id"], d["code_id"], d["created"], d["created_by"]))

        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is None:
            continue

        datasets.add(ds)

        item_id = d["item_id"]
        if item_id not in logdata:
            item_name = one_or_none(
                cur,
                f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
                (d["item_id"],)
            )
            logdata[item_id] = {
                "item": { "id": item_id, "name": item_name },
                "datatags": []
            }

        tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],))
        logdata[item_id]["datatags"].append({
            "user_id": d["created_by"],
            "tag": { "id": d["tag_id"], "name": tag_name },
        })

    stmt = (
        f"INSERT OR IGNORE INTO {TBL_DATATAGS} (item_id, tag_id, code_id, created, created_by) VALUES (?, ? , ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_DATATAGS} (id, item_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?, ?);"
    )
    cur.executemany(stmt, rows)

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "add datatags", list(logdata.values()), loguser)


def update_datatags(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = {}

    for d in data:
        ds = one_or_none(cur, f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["code_id"],))
        if ds is None:
            continue

        datasets.add(ds)

        item_id = d["item_id"]
        if item_id not in logdata:
            item_name = one_or_none(
                cur,
                f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
                (d["item_id"],)
            )
            logdata[item_id] = {
                "item": { "id": item_id, "name": item_name },
                "datatags": []
            }

        tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (d["tag_id"],))
        logdata[item_id]["datatags"].append({
            "user_id": d["created_by"],
            "tag": { "id": d["tag_id"], "name": tag_name },
        })


    cur.executemany(
        f"UPDATE {TBL_DATATAGS} SET tag_id = ? WHERE id = ?;",
        [(d["tag_id"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "update datatags", list(logdata.values()), loguser)


def update_item_datatags(cur, data, loguser=None):
    code_id = int(data["code_id"])
    user_id = int(data["user_id"])
    item_id = int(data["item_id"])
    created = data["created"]

    if "tags" not in data:
        return cur

    cleaned = [d for d in data["tags"] if d["created_by"] == user_id]

    tagsnow = cur.execute(
        f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ? AND created_by = ?;",
        (item_id, code_id, user_id)
    ).fetchall()

    existing = [d[0] for d in tagsnow]
    tokeep = [int(d["id"]) for d in cleaned if "id" in d]
    toremove = [id for id in existing if id not in tokeep]
    toadd = [int(d["tag_id"]) for d in cleaned if "id" not in d]

    # remove datatags not in the list
    if len(toremove) > 0:
        delete_datatags(cur, toremove, loguser)

    # add datatags where tags already exist in the database
    if len(toadd) > 0:
        add_datatags(cur, [{
            "item_id": item_id,
            "tag_id": tid,
            "code_id": code_id,
            "created": created,
            "created_by": user_id
        } for tid in toadd], loguser)

    return cur


def delete_datatags(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = {}

    for id in data:
        ds = one_or_none(cur,
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAGS} t ON t.code_id = c.id " +
            f"LEFT JOIN {TBL_DATATAGS} dt ON t.id = dt.tag_id WHERE dt.id = ?;",
            (id,)
        )

        if ds is None:
            continue

        datasets.add(ds)

        dt = cur.execute(
            f"SELECT item_id, tag_id, created_by FROM {TBL_DATATAGS} WHERE id = ?;",
            (id,)
        ).fetchone()

        if dt is not None:

            item_id = dt[0]
            if item_id not in logdata:
                item_name = one_or_none(
                    cur,
                    f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
                    (dt[0],)
                )
                logdata[item_id] = {
                    "item": { "id": item_id, "name": item_name },
                    "datatags": []
                }

            tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (dt[1],))
            logdata[item_id]["datatags"].append({
                "user_id": dt[2],
                "tag": { "id": dt[1], "name": tag_name }
            })

    cur.executemany(f"DELETE FROM {TBL_DATATAGS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "delete datatags", list(logdata.values()), loguser)


def delete_datatags_by_tags(cur, tags, loguser=None):
    if len(tags) == 0:
        return cur

    datasets = set()
    logdata = {}
    cleaned = []

    for id in tags:
        ds = get_dataset_id_by_tag(cur, id)
        if ds is None:
            continue

        datasets.add(ds)
        tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (id,))

        dt = cur.execute(
            f"SELECT item_id, created_by FROM {TBL_DATATAGS} WHERE tag_id = ?;",
            (id,)
        ).fetchall()

        for d in dt:
            item_id = d[0]
            if item_id not in logdata:
                item_name = one_or_none(
                    cur,
                    f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
                    (d[0],)
                )
                logdata[item_id] = {
                    "item": { "id": item_id, "name": item_name },
                    "datatags": []
                }

            logdata[item_id]["datatags"].append({
                "user_id": d[1],
                "tag": { "id": id, "name": tag_name },
            })

        cleaned.append((id,))

    cur.executemany(f"DELETE FROM {TBL_DATATAGS} WHERE tag_id = ?;", cleaned)

    for d in datasets:
        log_update(cur, TBL_DATATAGS, d)

    return log_action(cur, "delete datatags by tag", list(logdata.values()), loguser)



def get_evidence_by_dataset(cur, dataset):
    return cur.execute(
        f"""SELECT e.* from {TBL_EVIDENCE} e
            LEFT JOIN {TBL_ITEMS} i ON e.item_id = i.id
            WHERE i.dataset_id = ?;
        """,
        (dataset,),
    ).fetchall()


def get_evidence_by_code(cur, code):
    return cur.execute(f"SELECT * from {TBL_EVIDENCE} WHERE code_id = ?;", (code,)).fetchall()


def get_evidence_by_tag(cur, tag):
    return cur.execute(f"SELECT * from {TBL_EVIDENCE} WHERE tag_id = ?;", (tag,)).fetchall()


def add_evidence(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    with_id = "id" in data[0]
    datasets = set()

    for d in data:

        if "filepath" not in d:
            d["filepath"] = None
        if "tag_id" not in d:
            d["tag_id"] = None
        if "type" not in d:
            d["type"] = 1

        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is not None:
            datasets.add(ds)

        item_name = one_or_none(cur,
            f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
            (d["item_id"],))
        tag_name = one_or_none(cur,
            f"SELECT name FROM {TBL_TAGS} WHERE id = ?;",
            (d["tag_id"],))

        logdata.append({
            "type": d["type"],
            "description": d["description"],
            "item": { "id": d["item_id"], "name": item_name },
            "tag": { "id": d["tag_id"], "name": tag_name },
            "user_id": d["created_by"],
        })

    stmt = ""
    if with_id:
        stmt =f"""INSERT INTO {TBL_EVIDENCE} (
            id,
            item_id, code_id, tag_id,
            type,
            filepath,
            description,
            created,
            created_by
        ) VALUES (
            :id,
            :item_id, :code_id, :tag_id,
            :type,
            :filepath,
            :description,
            :created,
            :created_by
        );"""
    else:
        stmt =f"""INSERT INTO {TBL_EVIDENCE} (
            item_id, code_id, tag_id,
            type,
            filepath,
            description,
            created,
            created_by
        ) VALUES (
            :item_id, :code_id, :tag_id,
            :type,
            :filepath,
            :description,
            :created,
            :created_by
        );"""

    cur.executemany(stmt, data)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "add evidence", logdata, loguser)


def add_evidence_return_id(cur, d, loguser=None):
    if "filepath" not in d:
        d["filepath"] = None
    if "tag_id" not in d:
        d["tag_id"] = None
    if "type" not in d:
        d["type"] = 1

    id = one_or_none(
        cur,
        f"""INSERT INTO {TBL_EVIDENCE} (
            item_id, code_id, tag_id,
            type,
            filepath,
            description,
            created,
            created_by
        ) VALUES (
            :item_id, :code_id, :tag_id,
            :type,
            :filepath,
            :description,
            :created,
            :created_by
        ) RETURNING id;""",
        d,
    )

    # get data for logging
    item_name = one_or_none(cur,
        f"SELECT name FROM {TBL_ITEMS} WHERE id = ?;",
        (d["item_id"],)
    )
    tag_name = one_or_none(cur,
        f"SELECT name FROM {TBL_TAGS} WHERE id = ?;",
        (d["tag_id"],)
    )

    logdata = {
        "id": id,
        "type": d["type"],
        "description": d["description"],
        "item": { "id": d["item_id"], "name": item_name },
        "tag": { "id": d["tag_id"], "name": tag_name },
        "user_id": d["created_by"],
    }

    ds = get_dataset_id_by_code(cur, d["code_id"])
    log_update(cur, TBL_EVIDENCE, ds)
    log_action(cur, "add evidence", logdata, loguser)

    return id


def update_evidence(cur, data, base_path, loguser=None):
    if len(data) == 0:
        return

    before = cur.execute(
        f"SELECT filepath FROM {TBL_EVIDENCE} WHERE id IN ({make_space(len(data))});",
        [d["id"] for d in data],
    ).fetchall()

    rows = []
    datasets = set()
    dspaths = []
    logdata = []

    for r in data:
        if "filepath" not in r:
            r["filepath"] = None
        if "tag_id" not in r:
            r["tag_id"] = None
        if "type" not in r:
            r["type"] = None

        ds = get_dataset_id_by_code(cur, r["code_id"])
        dspaths.append(str(ds))
        if ds is not None:
            datasets.add(ds)

            rows.append((r["description"], r["filepath"], r["tag_id"], r["type"], r["id"]))
            tag_name = one_or_none(cur,
                f"SELECT name FROM {TBL_TAGS} WHERE id = ?;",
                (r["tag_id"],))

            logdata.append({
                "id": r["id"],
                "type": r["type"],
                "description": r["description"],
                "tag": { "id": r["tag_id"], "name": tag_name },
                "user_id": r["created_by"],
            })

    cur.executemany(
        f"UPDATE {TBL_EVIDENCE} SET description = ?, filepath = ?, tag_id = ?, type = ? WHERE id = ?;",
        rows
    )

    for i, d in enumerate(before):
        if d[0] is not None:
            has = cur.execute(f"SELECT id FROM {TBL_EVIDENCE} WHERE filepath = ?;", d).fetchone()
            if has is None:
                base_path.joinpath(dspaths[i], d[0]).unlink(missing_ok=True)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "update evidence", logdata, loguser)


def delete_evidence(cur, ids, base_path, loguser=None):
    if len(ids) == 0:
        return cur

    dspaths = []
    rows = []
    logdata = []
    datasets = set()

    for id in ids:
        ev = cur.execute(f"SELECT * FROM {TBL_EVIDENCE} WHERE id = ?;", (id,)).fetchone()
        if ev is not None:
            ds = get_dataset_id_by_code(cur, ev.code_id)

            if ds is not None:
                datasets.add(ds)
                dspaths.append(str(ds))

                rows.append(id)

                tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (ev.tag_id,))

                logdata.append({
                    "id": id,
                    "type": ev.type,
                    "description": ev.description,
                    "tag": { "id": ev.tag_id, "name": tag_name },
                    "user_id": ev.created_by,
                })


    filenames = cur.execute(
        f"SELECT filepath FROM {TBL_EVIDENCE} WHERE id IN ({make_space(len(rows))});", rows
    ).fetchall()
    cur.executemany(f"DELETE FROM {TBL_EVIDENCE} WHERE id = ?;", [(id,) for id in rows])

    for i, f in enumerate(filenames):
        if f is not None and f[0] is not None:
            has = cur.execute(f"SELECT id FROM {TBL_EVIDENCE} WHERE filepath = ?;", f).fetchone()
            if has is None:
                base_path.joinpath(dspaths[i], f[0]).unlink(missing_ok=True)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "delete evidence", logdata, loguser)


def delete_evidence_by_tag(cur, ids, base_path, loguser=None):
    if len(ids) == 0:
        return cur

    dspaths = []
    rows = []
    logdata = []
    filenames = []

    datasets = set()

    for id in ids:
        ds = get_dataset_id_by_tag(cur, id)
        if ds is None:
            continue

        datasets.add(ds)
        dspaths.append(str(ds))

        tag_name = one_or_none(cur, f"SELECT name FROM {TBL_TAGS} WHERE id = ?;", (id,))

        evs = cur.execute(
            f"SELECT id, filepath FROM {TBL_EVIDENCE} WHERE tag_id = ?;", (id,)
        ).fetchall()

        for ev in evs:
            rows.append((ev.id,))
            filenames.append(ev.filepath)

        logdata.append({
            "tag": { "id": id, "name": tag_name },
            "evidence_ids": [ev.id for ev in evs]
        })


    cur.executemany(f"DELETE FROM {TBL_EVIDENCE} WHERE id = ?;", rows)

    for i, f in enumerate(filenames):
        if f is not None and f[0] is not None:
            has = cur.execute(f"SELECT id FROM {TBL_EVIDENCE} WHERE filepath = ?;", f).fetchone()
            if has is None:
                base_path.joinpath(dspaths[i], f[0]).unlink(missing_ok=True)

    for d in datasets:
        log_update(cur, TBL_EVIDENCE, d)

    return log_action(cur, "delete evidence by tag", logdata, loguser)


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


def add_tag_assignments(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
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
            update_tag_assignments(cur, [o1, o2], loguser)
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

        logdata.append({
            "id": d["id"] if "id" in d else None,
            "old_code": d["old_code"],
            "new_code": d["new_code"],
            "old_tag": d["old_tag"],
            "new_tag": d["new_tag"]
        })

    remove_invalid_tag_assignments(cur)
    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "add tag assignments", logdata, loguser)


def update_tag_assignments(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    rows = []
    logdata = []
    datasets = set()

    for d in data:
        rows.append((d["new_tag"], d["description"], d["id"], d["old_code"], d["new_code"]))

        ds = get_dataset_id_by_code(cur, d["old_code"])
        if ds is not None:
            datasets.add(ds)

        logdata.append({
            "id": d["id"],
            "old_code": d["old_code"],
            "new_code": d["new_code"],
            "old_tag": d["old_tag"],
            "new_tag": d["new_tag"]
        })

    cur.executemany(
        f"UPDATE {TBL_TAG_ASS} SET new_tag = ?, description = ? WHERE id = ? AND old_code = ? AND new_code = ?;",
        rows,
    )
    remove_invalid_tag_assignments(cur)

    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "update tag assignments", logdata, loguser)


def delete_tag_assignments(cur, ids, loguser=None):
    if len(ids) == 0:
        return cur

    datasets = set()
    logdata = []

    for id in ids:

        ds = one_or_none(cur,
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TAG_ASS} t ON WHERE c.id = t.old_code WHERE t.id = ?;",
            (id,)
        )
        if ds is not None:
            datasets.add(ds)

            ta = one_or_none(cur,
                f"SELECT (id,old_code,new_code,old_tag,new_tag) FROM {TBL_TAG_ASS} WHERE id = ?;",
                (id,)
            )

            logdata.append({
                "id": ta[0],
                "old_code": ta[1],
                "new_code":ta[2],
                "old_tag": ta[3],
                "new_tag": ta[4],
            })

    cur.executemany(f"DELETE FROM {TBL_TAG_ASS} WHERE id = ?;", [(id,) for id in ids])
    remove_invalid_tag_assignments(cur)

    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "delete tag assignments", logdata, loguser)


def delete_tag_assignments_by_tag(cur, ids, loguser=None):
    if len(ids) == 0:
        return cur

    datasets = set()
    logdata = []

    for id in ids:
        ds = get_dataset_id_by_tag(cur, id)
        if ds is None:
            continue

        datasets.add(ds)

        taids = cur.execute(
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_tag = ? OR new_tag = ?;", (id,id)
        ).fetchall()

        for ta in taids:
            logdata.append({ "id": ta[0] })

    cur.executemany(
        f"DELETE FROM {TBL_TAG_ASS} WHERE id = ?;", [(d["id"],) for d in logdata]
    )

    remove_invalid_tag_assignments(cur)

    for d in datasets:
        log_update(cur, TBL_TAG_ASS, d)

    return log_action(cur, "delete tag assignments by tag", logdata, loguser)


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


def add_code_transitions(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    rows = []
    logdata = []
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

        logdata.append({
            "id": d["id"] if "id" in d else None,
            "old_code": d["old_code"],
            "new_code": d["new_code"],
        })

    stmt = (
        f"INSERT INTO {TBL_TRANS} (old_code, new_code, started, finished) VALUES (?, ?, ?, ?);"
        if not with_id
        else f"INSERT INTO {TBL_TRANS} (id, old_code, new_code, started, finished) VALUES (?, ?, ?, ?, ?);"
    )

    cur.executemany(stmt, rows)

    for d in datasets:
        log_update(cur, TBL_TRANS, d)

    return log_action(cur, "add code transitions", logdata, loguser)


def update_code_transitions(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    datasets = set()

    for d in data:
        ds_old = cur.execute(
            f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (d["old_code"],)
        ).fetchone()
        datasets.add(ds_old[0])

        logdata.append({
            "id": d["id"],
            "old_code": d["old_code"],
            "new_code": d["new_code"],
            "finished": d["finished"]
        })

    cur.executemany(
        f"UPDATE {TBL_TRANS} SET finished = ? WHERE id = ?;",
        [(d["finished"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_TRANS, d)

    return log_action(cur, "update code transitions", logdata, loguser)


def delete_code_transitions(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = []

    for id in data:
        ds = one_or_none(cur,
            f"SELECT dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_TRANS} t ON c.id = t.old_code WHERE t.id = ?;",
            (id,)
        )
        if ds is not None:
            datasets.add(ds)

        ct = one_or_none(cur, f"SELECT id, old_code, new_code FROM {TBL_TRANS} WHERE id = ?;", (id,))
        if ct is not None:
            logdata.append({
                "id": ct["id"],
                "old_code": ct["old_code"],
                "new_code": ct["new_code"],
                "finished": ct["finished"]
            })

    cur.executemany(f"DELETE FROM {TBL_TRANS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_TRANS, d)

    return log_action(cur, "delete code transitions", logdata, loguser)


def prepare_transition(cur, old_code, new_code, loguser=None):
    ds_old = one_or_none(cur, f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (old_code,))
    ds_new = one_or_none(cur, f"SELECT dataset_id FROM {TBL_CODES} WHERE id = ?;", (new_code,))

    if ds_old is None or ds_new is None or ds_old != ds_new:
        raise ValueError("incompatible or missing codes")

    log_action(
        cur,
        "prepare code transitions",
        { "old_code": old_code, "new_code": new_code },
        loguser
    )

    old_tags = get_tags_by_code(cur, old_code)
    assigned = {}

    rows = []
    # create/copy tags from old code that do not have a parent
    for t in old_tags:

        # check if a tag assignment alraady exists
        tag_assigned_id = one_or_none(
            cur,
            f"SELECT id FROM {TBL_TAG_ASS} WHERE old_code = ? AND new_code = ? AND old_tag = ?;",
            (old_code, new_code, t.id)
        )

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
                loguser
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
                loguser
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
        add_datatags(cur, rows, loguser)

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
                loguser
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
            assigned_evs[d.id] = add_evidence_return_id(cur, obj, loguser)
            num += 1

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
                f"""SELECT ec1.id FROM {TBL_META_CATS} ec1
                INNER JOIN {TBL_META_CATS} ec2 ON ec1.parent = ec2.id
                WHERE ec2.name = ? AND ec1.name = ? AND ec1.created_by = ? AND ec1.code_id = ?;
                """,
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
                loguser
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
                group_id = add_meta_group_return_id(cur, as_obj, loguser)

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
            add_meta_items(cur, rows, loguser)
            num += len(rows)

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


def add_meta_groups(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    counts = {}
    datasets = set()

    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is None:
            continue

        datasets.add(ds)

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

        logdata.append({
            "name": d["name"],
            "description": d["description"],
            "item_id": d["item_id"],
            "code_id": d["code_id"],
            "user_id": d["created_by"]
        })

    cur.executemany(
        f"INSERT INTO {TBL_META_GROUPS} (name, item_id, code_id, name, description, created, created_by) "
        + "VALUES (:name, :item_id, :code_id, :name, :description, :created, :created_by);",
        data,
    )

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "add meta groups", logdata, loguser)


def update_meta_groups(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    datasets = set()

    for d in data:

        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is None:
            continue

        datasets.add(ds)

        logdata.append({
            "id": d["id"],
            "item_id": d["item_id"],
            "name": d["name"],
            "description": d["description"]
        })

    cur.executemany(
        f"UPDATE {TBL_META_GROUPS} SET name = ? WHERE id = ?;",
        [(d["name"], d["id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "update meta groups", logdata, loguser)


def add_meta_group_return_id(cur, d, loguser=None):
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

    ds = get_dataset_id_by_code(cur, d["code_id"])

    log_update(cur, TBL_META_GROUPS, ds)
    log_action(cur, "add meta groups", {
        "id": id,
        "name": d["name"],
        "description": d["description"],
        "item_id": d["item_id"],
        "code_id": d["code_id"],
        "user_id": d["created_by"]
    }, loguser)

    return id


def delete_meta_groups(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    datasets = set()

    for id in data:
        ds = one_or_none(cur,
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (id,)
        )
        if ds is not None:
            datasets.add(ds)

        mg = one_or_none(cur,
            f"SELECT item_id, name, description FROM {TBL_META_GROUPS} WHERE id = ?,",
            (id,)
        )
        if mg is not None:
            logdata.append({
                "id": id,
                "item_id": mg[0],
                "name": mg[1],
                "description": mg[2]
            })

    cur.executemany(f"DELETE FROM {TBL_META_GROUPS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_GROUPS, d)

    return log_action(cur, "delete meta groups", logdata, loguser)


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


def add_meta_item_return_id(cur, d, loguser=None):
    if "group_id" not in d or d["group_id"] is None:
        d["group_id"] = add_meta_group_return_id(cur, d, loguser)

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
    id = parse(res, "id")

    if "categories" in d:
        for c in d["categories"]:
            c["meta_id"] = id
        add_meta_cat_conns(cur, d["categories"], loguser)
    if "tags" in d:
        for t in d["tags"]:
            t["meta_id"] = id
        add_meta_tag_conns(cur, d["tags"], loguser)
    if "evidence" in d:
        for t in d["evidence"]:
            t["meta_id"] = id
        add_meta_ev_conns(cur, d["evidence"], loguser)

    return id


def add_meta_items(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    datasets = set()

    for d in data:

        if "group_id" not in d or d["group_id"] is None:
            d["group_id"] = add_meta_group_return_id(cur, d, loguser)

        if "cluster" not in d or d["cluster"] is None:
            d["cluster"] = "misc"

        ds = cur.execute(
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} t ON c.id = t.code_id WHERE t.id = ?;",
            (d["group_id"],),
        ).fetchone()
        if ds is None:
            continue

        datasets.add(ds[0])

        id = add_meta_item_return_id(cur, d, loguser)
        logdata.append({
            "id": id,
            "group_id": d["group_id"],
            "name": d["name"],
            "cluster": d["cluster"],
            "description": d["description"],
            "user_id": d["created"]
        })

    for d in datasets:
        log_update(cur, TBL_META_ITEMS, d)

    return log_action(cur, "add meta items", logdata, loguser)


def update_meta_items(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
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

            logdata.append({
                "item_id": d["item_id"],
                "name": d["name"],
                "cluster": d["cluster"],
                "user_id": d["created_by"]
            })

            # check if old group is empty, if yes: delete it
            if old_group != d["group_id"]:
                exists = cur.execute(
                    f"SELECT 1 FROM {TBL_META_ITEMS} WHERE group_id = ?;", (old_group,)
                ).fetchone()
                if exists is None:
                    delete_meta_groups(cur, [old_group], loguser)

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

            delete_meta_cat_conns(cur, to_remove, loguser)

            to_add = []
            # add new categories not previously used
            for c in d["categories"]:
                if c["cat_id"] in diff2:
                    c["meta_id"] = d["id"]
                    to_add.append(c)

            add_meta_cat_conns(cur, to_add, loguser)

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

            delete_meta_tag_conns(cur, to_remove, loguser)

            to_add = []
            # add new tags not previously used
            for t in d["tags"]:
                if t["tag_id"] in diff2:
                    t["meta_id"] = d["id"]
                    to_add.append(t)

            add_meta_tag_conns(cur, to_add, loguser)

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

            delete_meta_ev_conns(cur, to_remove, loguser)

            to_add = []
            # add new tags not previously used
            for e in d["evidence"]:
                if e["ev_id"] in diff2:
                    e["meta_id"] = d["id"]
                    to_add.append(e)

            add_meta_ev_conns(cur, to_add, loguser)

    for d in datasets:
        log_update(cur, TBL_META_ITEMS, d)

    return log_action(cur, "update meta items", logdata, loguser)


def delete_meta_items(cur, data, loguser=None):
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
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_ITEMS, d)

        log_action(cur, "delete meta items", {"ids": data}, loguser)

    cur.executemany(f"DELETE FROM {TBL_META_CON_CAT} WHERE meta_id = ?;", [(id,) for id in data])
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_CAT, d)
        log_action(cur, "delete meta cat connections", {"count": cur.rowcount}, loguser)

    cur.executemany(f"DELETE FROM {TBL_META_CON_TAG} WHERE meta_id = ?;", [(id,) for id in data])
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_TAG, d)
        log_action(cur, "delete meta tag connections", {"count": cur.rowcount}, loguser)

    cur.executemany(f"DELETE FROM {TBL_META_CON_EV} WHERE meta_id = ?;", [(id,) for id in data], loguser)
    if cur.rowcount > 0:
        for d in datasets:
            log_update(cur, TBL_META_CON_EV, d)
        log_action(cur, "delete meta evidence connections", {"count": cur.rowcount}, loguser)

    to_del = []
    for id in groups:
        res = cur.execute(f"SELECT id FROM {TBL_META_ITEMS} WHERE group_id = ?;", (id,)).fetchone()
        if res is None:
            to_del.append(id)

    return delete_meta_groups(cur, to_del, loguser)


def get_meta_categories_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_META_CATS} WHERE code_id = ?;", (code,)).fetchall()


def get_meta_categories_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT m.* FROM {TBL_META_CATS} m LEFT JOIN {TBL_CODES} c ON m.code_id = c.id WHERE c.dataset_id = ?;",
        (dataset,),
    ).fetchall()


def add_meta_categories(cur, dataset, code, data, loguser):
    if len(data) == 0:
        return cur

    logdata = []

    for d in data:
        if "parent" not in d:
            d["parent"] = None

        d["dataset_id"] = dataset
        d["code_id"] = code

        logdata.append({
            "name": d["name"],
            "description": d["description"],
            "parent": d["parent"],
            "user_id": d["created_by"],
            "code_id": code,
        })

    cur.executemany(
        f"""INSERT INTO {TBL_META_CATS} (
            name,
            description,
            parent,
            created,
            created_by,
            dataset_id,
            code_id
        ) VALUES (
            :name,
            :description,
            :parent,
            :created,
            :created_by,
            :dataset_id,
            :code_id
        );""",
        data,
    )

    log_update(cur, TBL_META_CATS, dataset)
    return log_action(cur, "add meta categories", logdata, loguser)


def add_meta_category_return_id(cur, data, loguser=None):
    cat = cur.execute(
        f"""INSERT INTO {TBL_META_CATS} (
            name,
            description,
            parent,
            created,
            created_by,
            dataset_id,
            code_id
        ) VALUES (
            :name,
            :description,
            :parent,
            :created,
            :created_by,
            :dataset_id,
            :code_id
        ) RETRUNING id;""",
        data,
    ).fetchone()

    log_update(cur, TBL_META_CATS, data["dataset_id"])
    log_action(
        cur, "add meta category", {
            "name": data["name"],
            "description": data["description"],
            "parent": data["parent"],
            "user_id": data["created_by"],
            "code_id": data["code_id"],
        },
        loguser
    )
    return cat[0]


def update_meta_categories(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = []

    for d in data:
        if "parent" not in d:
            d["parent"] = None

        ds = get_dataset_id_by_code(cur, d["code_id"])
        if ds is not None:
            datasets.add(ds)

            logdata.append({
                "name": d["name"],
                "description": d["description"],
                "parent": d["parent"],
            })

    cur.executemany(
        f"UPDATE {TBL_META_CATS} SET name = :name, description = :description, parent = :parent WHERE id = :id;",
        data,
    )

    for d in datasets:
        log_update(cur, TBL_META_CATS, d)

    return log_action(cur, "update meta categories", logdata, loguser)


def delete_meta_categories(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = []

    for id in data:
        ds = one_or_none(cur,
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_CATS} m ON c.id = m.code_id WHERE m.id = ?;",
            (id,),
        )

        if ds is not None:
            datasets.add(ds)

        mc = one_or_none(cur, f"SELECT name {TBL_META_CATS} WHERE id = ?;", (id,))

        if mc is not None:
            logdata.append({ "id": id, "name": mc[0] })

    cur.executemany(f"DELETE FROM {TBL_META_CATS} WHERE id = ?;", [(id,) for id in data])

    for d in datasets:
        log_update(cur, TBL_META_CATS, d)

    return log_action(cur, "delete meta categories", logdata, loguser)


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


def add_meta_cat_conns(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        group = one_or_none(cur,
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;",
            (d["meta_id"],)
        )
        ds = one_or_none(cur,
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} m ON c.id = m.code_id WHERE m.id = ?;",
            (group,),
        )
        if ds is not None:
            datasets.add(ds)

    cur.executemany(
        f"INSERT INTO {TBL_META_CON_CAT} (meta_id, cat_id) VALUES (?, ?);",
        [(d["meta_id"], d["cat_id"]) for d in data],
    )

    for d in datasets:
        log_update(cur, TBL_META_CON_CAT, d)

    return log_action(
        cur,
        "add meta cat connections",
        [{ "meta_id": d["meta_id"], "cat_id": d["cat_id"] } for d in data],
        loguser
    )


def delete_meta_cat_conns(cur, data, loguser=None):
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

    return log_action(cur, "delete meta cat connections", {"ids": data}, loguser)


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


def add_meta_tag_conns(cur, data, loguser=None):
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

    return log_action(
        cur,
        "add meta tag connections",
        [{ "meta_id": d["meta_id"], "tag_id": d["tag_id"] } for d in data],
        loguser
    )


def delete_meta_tag_conns(cur, data, loguser=None):
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

    return log_action(cur, "delete meta tag connections", {"ids": data}, loguser)


def delete_meta_tag_conns_by_tag(cur, ids, loguser=None):
    if len(ids) == 0:
        return cur

    datasets = set()
    cleaned = []

    for id in ids:
        ds = get_dataset_id_by_tag(cur, id)
        if ds is None:
            continue

        datasets.add(ds)
        cleaned.append((id,))

    cur.executemany(f"DELETE FROM {TBL_META_CON_TAG} WHERE tag_id = ?;", cleaned)

    for d in datasets:
        log_update(cur, TBL_META_CON_TAG, d)

    return log_action(cur, "delete meta tag connections by tags", {"tags": ids}, loguser)


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


def add_meta_ev_conns(cur, data, loguser=None):
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

    return log_action(
        cur,
        "add meta evidence connections",
        [{ "meta_id": d["meta_id"], "ev_id": d["ev_id"] } for d in data],
        loguser
    )


def delete_meta_ev_conns(cur, data, loguser=None):
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

    return log_action(cur, "delete meta evidence connections", {"ids": data}, loguser)


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


def add_meta_agreements(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    logdata = []
    datasets = set()

    for d in data:

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

        logdata.append({
            "meta_id": d["meta_id"],
            "item_id": item_id,
            "user_id": d["created_by"],
            "value": d["value"]
        })

    cur.executemany(
        f"INSERT INTO {TBL_META_AG} (meta_id, created_by, value) VALUES (:meta_id, :created_by, :value);",
        data,
    )
    for d in datasets:
        log_update(cur, TBL_META_AG, d)

    return log_action(cur, "add meta agreements", logdata, loguser)


def update_meta_agreements(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    logdata = []

    for d in data:
        group = one_or_none(cur,
            f"SELECT group_id FROM {TBL_META_ITEMS} WHERE id = ?;",
            (d["meta_id"],)
        )
        if group is None:
            continue

        ds = one_or_none(cur,
            f"SELECT c.dataset_id FROM {TBL_CODES} c LEFT JOIN {TBL_META_GROUPS} g ON c.id = g.code_id WHERE g.id = ?;",
            group,
        )

        if ds is not None:
            datasets.add(ds)

        logdata.append({
            "id": d["id"],
            "meta_id": d["meta_id"],
            "user_id": d["created_by"],
            "value": d["value"]
        })

    cur.executemany(
        f"UPDATE {TBL_META_AG} SET value = ? WHERE id = ?;", [(d["value"], d["id"]) for d in data]
    )
    for d in datasets:
        log_update(cur, TBL_META_AG, d)

    return log_action(cur, "update meta agreements", logdata, loguser)


def delete_meta_agreements(cur, data, loguser=None):
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

    return log_action(cur, "delete meta agreements", {"ids": data}, loguser)

###########################################
## OBJECTIONS
###########################################

def get_objections_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT s.* from {TBL_OBJECT} s LEFT JOIN {TBL_CODES} c ON s.code_id = c.id WHERE c.dataset_id = ? ORDER BY s.status DESC, s.id ASC;",
        (dataset,)
    ).fetchall()


def get_objections_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_OBJECT} WHERE code_id = ? ORDER BY status DESC, id ASC;", (code,)).fetchall()


def add_objections(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()

    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        datasets.add(ds)

        if "item_id" not in d:
            d["item_id"] = None

        if "tag_id" not in d:
            d["tag_id"] = None

        if "status" not in d:
            d["status"] = OBJ_STATUS_OPEN

        if "resolution" not in d:
            d["resolution"] = None
        if "resolved" not in d:
            d["resolved"] = None
        if "resolved_by" not in d:
            d["resolved_by"] = None

    cur.executemany(
        f"INSERT INTO {TBL_OBJECT} (user_id, code_id, item_id, tag_id, action, status, explanation, resolution, created) " +
        "VALUES (:user_id, :code_id, :item_id, :tag_id, :action, :status, :explanation, :resolution, :created);",
        data
    )

    for d in datasets:
        log_update(cur, TBL_OBJECT, d)

    return log_action(
        cur,
        "add objections",
        [
            {
                "user_id": d["user_id"],
                "item_id": d["item_id"],
                "code_id": d["code_id"],
                "tag_id": d["tag_id"],
                "action": d["action"],
                "status": d["status"],
                "explanation": d["explanation"],
            } for d in data
        ],
        loguser
    )


def update_objections(cur, data, loguser=None):
    if len(data) == 0:
        return cur

    datasets = set()
    valid = []

    for d in data:
        if d["resolved_by"] is None or d["resolved_by"] is not d["user_id"]:
            valid.append(d)

            ds = get_dataset_id_by_code(cur, d["code_id"])
            datasets.add(ds)

    cur.executemany(
        f"UPDATE {TBL_OBJECT} SET status = ?, action = ?, explanation = ?, resolution = ?, " +
        "resolved_by = ?, resolved = ?, item_id = ?, tag_id = ? WHERE id = ?;",
        [(
            d["status"],
            d["action"],
            d["explanation"],
            d["resolution"],
            d["resolved_by"],
            d["resolved"],
            d["item_id"],
            d["tag_id"],
            d["id"]
        ) for d in valid]
    )

    for d in datasets:
        log_update(cur, TBL_OBJECT, d)

    return log_action(
        cur,
        "update objections",
        [
            {
                "id": d["id"],
                "user_id": d["user_id"],
                "item_id": d["item_id"],
                "code_id": d["code_id"],
                "tag_id": d["tag_id"],
                "action": d["action"],
                "status": d["status"],
                "explanation": d["explanation"],
                "resolution": d["resolution"],
                "resolved_by": d["resolved_by"]
            } for d in valid
        ],
        loguser
    )


def delete_objections(cur, ids, loguser=None):
    if len(ids) == 0:
        return cur

    datasets = set()
    for id in ids:
        code_id = one_or_none(cur, f"SELECT code_id FROM {TBL_OBJECT} WHERE id = ?;", (id,))
        if code_id is not None:
            ds = get_dataset_id_by_code(cur, code_id)
            datasets.add(ds)

    cur.executemany(f"DELETE FROM {TBL_OBJECT} WHERE id = ?;", [(id,) for id in ids])

    for d in datasets:
        log_update(cur, TBL_OBJECT, d)

    return log_action(cur, "delete objections", { "ids": ids }, loguser)


###########################################
## GAME SCORES STUFF
###########################################

def get_game_scores_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT s.* from {TBL_SCORES} s LEFT JOIN {TBL_CODES} c ON s.code_id = c.id WHERE c.dataset_id = ? ORDER BY s.id;",
        (dataset,)
    ).fetchall()


def get_game_scores_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_SCORES} WHERE code_id = ?;", (code,)).fetchall()


def add_game_scores(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()

    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        datasets.add(ds)

        # get existing record
        existing = cur.execute(
            f"SELECT * FROM {TBL_SCORES} WHERE game_id = ? AND difficulty = ? AND code_id = ? AND user_id = ?;",
            (d["game_id"], d["difficulty"], d["code_id"], d["user_id"])
        ).fetchone()

        if existing is None:
            # add new record
            d["played"] = 1
            d["wins"] = 1 if d["win"] else 0
            d["avg_score"] = float(d["score"])
            d["streak_current"] = 1 if d["win"] else 0
            d["streak_highest"] = 1 if d["win"] else 0
            cur.execute(
                f"INSERT INTO {TBL_SCORES} (game_id, difficulty, code_id, user_id, played, wins, avg_score, streak_current, streak_highest) " +
                "VALUES (:game_id, :difficulty, :code_id, :user_id, :played, :wins, :avg_score, :streak_current, :streak_highest);",
                d
            )
        else:
            # update existing record
            asd = existing._asdict()
            asd["avg_score"] = (asd["avg_score"] * float(asd["played"]) + float(d["score"])) / float(asd["played"] + 1)
            asd["played"] += 1
            if d["win"]:
                asd["wins"] += 1
                asd["streak_current"] += 1
                if asd["streak_current"] > asd["streak_highest"]:
                    asd["streak_highest"] = asd["streak_current"]
            else:
                asd["streak_current"] = 0

            update_game_scores(cur, [asd])


    for d in datasets:
        log_update(cur, TBL_SCORES, d)

    return cur


def update_game_scores(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        datasets.add(ds)

    cur.executemany(
        f"UPDATE {TBL_SCORES} SET played = ?, wins = ?, avg_score = ?, streak_current = ?, streak_highest = ? WHERE id = ?;",
        [(d["played"], d["wins"], d["avg_score"], d["streak_current"], d["streak_highest"], d["id"]) for d in data]
    )

    for d in datasets:
        log_update(cur, TBL_SCORES, d)

    return cur


def get_game_scores_items_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT s.* from {TBL_SCORES_ITEMS} s LEFT JOIN {TBL_CODES} c ON s.code_id = c.id WHERE c.dataset_id = ? ORDER BY s.created DESC;",
        (dataset,)
    ).fetchall()


def get_game_scores_items_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_SCORES_ITEMS} WHERE code_id = ?;", (code,)).fetchall()


def add_game_scores_items(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    now = get_millis()

    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        datasets.add(ds)

        d["win"] = 1 if d["win"] else 0

        if "created" not in d or d["created"] is None:
            d["created"] = now

    cur.executemany(
        f"INSERT INTO {TBL_SCORES_ITEMS} (game_id, difficulty, code_id, user_id, item_id, created, win) " +
        "VALUES (:game_id, :difficulty, :code_id, :user_id, :item_id, :created, :win);",
        data
    )

    for d in datasets:
        log_update(cur, TBL_SCORES_ITEMS, d)

    return cur


def get_game_scores_tags_by_dataset(cur, dataset):
    return cur.execute(
        f"SELECT s.* from {TBL_SCORES_TAGS} s LEFT JOIN {TBL_CODES} c ON s.code_id = c.id WHERE c.dataset_id = ? ORDER BY s.created DESC;",
        (dataset,)
    ).fetchall()


def get_game_scores_tags_by_code(cur, code):
    return cur.execute(f"SELECT * FROM {TBL_SCORES_TAGS} WHERE code_id = ?;", (code,)).fetchall()


def add_game_scores_tags(cur, data):
    if len(data) == 0:
        return cur

    datasets = set()
    now = get_millis()

    for d in data:
        ds = get_dataset_id_by_code(cur, d["code_id"])
        datasets.add(ds)

        d["win"] = 1 if d["win"] else 0

        if "created" not in d or d["created"] is None:
            d["created"] = now

    cur.executemany(
        f"INSERT INTO {TBL_SCORES_TAGS} (game_id, difficulty, code_id, user_id, tag_id, item_id, created, win) " +
        "VALUES (:game_id, :difficulty, :code_id, :user_id, :tag_id, :item_id, :created, :win);",
        data
    )

    for d in datasets:
        log_update(cur, TBL_SCORES_TAGS, d)

    return cur


def log_visible_warnings(cur, data, loguser=None):
    if "user_id" in data and "code_id" in data \
        and "item" in data and "warnings" in data :
        return log_action(cur, "visible warnings", data, loguser)

    return cur

