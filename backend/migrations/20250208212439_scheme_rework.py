"""
This module contains a Caribou migration.

Migration Name: scheme_rework
Migration Version: 20250208212439
"""
import os
import json
from pathlib import Path

SCHEME_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "dist", "schemes")
SCHEME_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "schemes")

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_meta_scheme(cur, dataset, path, backup_path):
    res = cur.execute("SELECT meta_scheme FROM datasets WHERE id = ?;", (dataset,)).fetchone()
    if res is None:
        return None

    p = res["meta_scheme"] if isinstance(res, dict) else res[0]
    if not p.endswith(".json"):
        p += ".json"

    obj = None

    try:
        with open(path.joinpath(p), "r") as file:
            obj = json.load(file)
        return obj
    except:
        print("scheme not in base folder")

    try:
        with open(backup_path.joinpath(p), "r") as file:
            obj = json.load(file)
        return obj
    except:
        print("scheme not in backup folder")

    return obj

def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all datasets
    datasets = cur.execute("SELECT * FROM datasets").fetchall()

    # modify schema data
    for d in datasets:
        scheme = get_meta_scheme(cur, d["id"], SCHEME_PATH, SCHEME_BACKUP)
        d["item_name"] = scheme["item_name"]
        d["meta_item_name"] = scheme["meta_item_name"]
        del scheme["item_name"]
        del scheme["meta_item_name"]
        d["schema"] = bytes(json.dumps(scheme), 'utf-8')

    # delete old dataset table
    cur.execute("DELETE FROM datasets;")
    cur.execute("DROP TABLE datasets;")

    # create dataset table
    cur.execute("""CREATE TABLE datasets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        item_name TEXT NOT NULL,
        meta_item_name TEXT,
        meta_table TEXT,
        description TEXT,
        schema BLOB
    );""")

    # add datasets again
    for d in datasets:
        cur.execute(
            "INSERT INTO datasets (id, name, item_name, meta_item_name, meta_table, " +
            "description, schema) VALUES (:id, :name, :item_name, :meta_item_name, :meta_table, " +
            ":description, :schema);",
            d
        )

    connection.commit()

def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all datasets
    datasets = cur.execute("SELECT * FROM datasets").fetchall()

    # delete old dataset table
    cur.execute("DELETE FROM datasets;")
    cur.execute("DROP TABLE datasets;")

    # create dataset table
    cur.execute("""CREATE TABLE datasets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        meta_table TEXT,
        meta_scheme TEXT,
        description TEXT
    );""")

    # add datasets again
    for d in datasets:
        scheme = json.loads(d["schema"].decode('utf-8'))
        scheme["item_name"] = d["item_name"]
        scheme["meta_item_name"] = d["meta_item_name"]

        del d["item_name"]
        del d["meta_item_name"]
        d["meta_scheme"] = f"scheme_{d['id']}"

        cur.execute(
            "INSERT INTO datasets (id, name, meta_table, meta_scheme, description) " +
            "VALUES (:id, :name, :meta_table, :meta_scheme, :description);",
            d
        )

        with open(SCHEME_PATH.joinpath(d["meta_scheme"]+".json"), "w") as file:
            json.dump(scheme, file)

        with open(SCHEME_BACKUP.joinpath(d["meta_scheme"]+".json"), "w") as file:
            json.dump(scheme, file)

    connection.commit()
