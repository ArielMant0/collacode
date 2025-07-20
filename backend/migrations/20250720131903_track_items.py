"""
This module contains a Caribou migration.

Migration Name: track_items
Migration Version: 20250720131903
"""

from datetime import datetime, timezone

TBL_DATASETS = "datasets"
TBL_USERS = "users"
TBL_PRJ_USERS = "project_users"
TBL_ITEMS = "items"
TBL_CODES = "codes"
TBL_DATATAGS = "datatags"

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # for each dataset
    datasets = cur.execute(f"SELECT * FROM {TBL_DATASETS}").fetchall()

    all_items = []
    now = int(datetime.now(timezone.utc).timestamp() * 1000)

    for ds in datasets:
        # get all users for this dataset
        users = cur.execute(f"SELECT * FROM {TBL_PRJ_USERS} WHERE dataset_id = ?", (ds["id"],)).fetchall()
        # get all items for this dataset
        items = cur.execute(f"SELECT * FROM {TBL_ITEMS} WHERE dataset_id = ?", (ds["id"],)).fetchall()
        # get all codes for this dataset
        codes = cur.execute(f"SELECT * FROM {TBL_CODES} WHERE dataset_id = ?", (ds["id"],)).fetchall()

        # for each item, find out which code its first datatag belongs to
        for it in items:

            # assume the first code is where an item was added
            first_code = codes[0]["id"]
            # assume the first project user created this item
            first_user = users[0]["user_id"]

            for c in codes:

                item_tags = cur.execute(
                    f"SELECT * FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ?",
                    (it["id"], c["id"])
                ).fetchall()

                # the item has tags for this code, so we can break the loop
                if len(item_tags) > 0:
                    first_code = c["id"]
                    first_user = item_tags[0]["created_by"]
                    break

            it["code_id"] = first_code
            it["created"] = now
            it["created_by"] = first_user

        all_items = all_items + items

    # delete tables
    cur.execute(f"DELETE FROM {TBL_ITEMS}")
    cur.execute(f"DROP TABLE {TBL_ITEMS}")

    # create new tables
    cur.execute(
        f"""CREATE TABLE {TBL_ITEMS} (
            id  INTEGER PRIMARY KEY,
            dataset_id  INTEGER NOT NULL,
            code_id  INTEGER NOT NULL,
            created  INTEGER NOT NULL,
            created_by  INTEGER NOT NULL,
            name    TEXT NOT NULL,
            description TEXT,
            url TEXT,
            teaser  TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
            FOREIGN KEY(code_id) REFERENCES codes (id) ON DELETE CASCADE
        )"""
    )

    # add new data to items
    cur.executemany(
        f"INSERT INTO {TBL_ITEMS} (id, dataset_id, code_id, created, created_by, name, description, url, teaser) " +
        "VALUES (:id, :dataset_id, :code_id, :created, :created_by, :name, :description, :url, :teaser);",
        all_items,
    )

    # commit changes
    connection.commit()

def downgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all items
    items = cur.execute(f"SELECT * FROM {TBL_ITEMS}").fetchall()

    # delete tables
    cur.execute(f"DELETE FROM {TBL_ITEMS}")
    cur.execute(f"DROP TABLE {TBL_ITEMS}")

    # create new tables
    cur.execute(
        f"""CREATE TABLE {TBL_ITEMS} (
            id  INTEGER PRIMARY KEY,
            dataset_id  INTEGER NOT NULL,
            name    TEXT NOT NULL,
            description TEXT,
            url TEXT,
            teaser  TEXT,
            FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
        )"""
    )

    # add new data to items
    cur.executemany(
        f"INSERT INTO {TBL_ITEMS} (id, dataset_id, name, description, url, teaser) " +
        "VALUES (:id, :dataset_id, :name, :description, :url, :teaser);",
        items,
    )

    # commit changes
    connection.commit()
