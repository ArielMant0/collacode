"""
This module contains a Caribou migration.

Migration Name: projects
Migration Version: 20250107182820
"""
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_steam_id(url):
    if "store.steampowered.com" not in url:
        return None

    app_idx = url.find("app/")
    if app_idx < 0:
        return None

    last_idx = url.rfind("/", app_idx+4)
    if last_idx < 0:
        return None

    return int(url[app_idx+4:last_idx])

def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ds = cur.execute("SELECT * FROM datasets;").fetchall()
    games = cur.execute("SELECT * FROM games;").fetchall()
    exp = cur.execute("SELECT * FROM game_expertise;").fetchall()
    dts = cur.execute("SELECT * FROM datatags;").fetchall()
    ev = cur.execute("SELECT * FROM evidence;").fetchall()
    ext_g = cur.execute("SELECT * FROM ext_groups;").fetchall()
    ext = cur.execute("SELECT * FROM externalizations;").fetchall()

    cur.execute("DELETE FROM datasets;")
    cur.execute("DELETE FROM games;")
    cur.execute("DELETE FROM game_expertise;")
    cur.execute("DELETE FROM datatags;")
    cur.execute("DELETE FROM evidence;")
    cur.execute("DELETE FROM ext_groups;")

    cur.execute("DROP TABLE datasets;")
    cur.execute("DROP TABLE game_expertise;")
    cur.execute("DROP TABLE datatags;")
    cur.execute("DROP TABLE evidence;")
    cur.execute("DROP TABLE ext_groups;")

    # --------------------------
    # re-add datasets table
    # --------------------------

    cur.execute("""CREATE TABLE datasets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        meta_table TEXT,
        description TEXT
    );""")

    for d in ds:
        if "meta_table" not in d:
            d["meta_table"] = "games_data"
        if "description" not in d:
            d["description"] = None

    # add datasets again
    cur.executemany(
        "INSERT INTO datasets (id, name, meta_table, description) VALUES (:id, :name, :meta_table, :description);",
        ds
    )

    # --------------------------
    # re-add all tables referencing games
    # --------------------------

    cur.execute("""CREATE TABLE items (
        id  INTEGER PRIMARY KEY,
        name	TEXT NOT NULL,
	    dataset_id	INTEGER NOT NULL,
        url TEXT,
        teaser	TEXT,
	    FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE
    );""")

    # add games again
    cur.executemany(
        "INSERT INTO items (id, name, dataset_id, url, teaser) VALUES (:id, :name, :dataset_id, :url, :teaser);",
        games
    )

    cur.execute("""CREATE TABLE expertise (
        id	INTEGER PRIMARY KEY,
        item_id	INTEGER NOT NULL,
        user_id	INTEGER NOT NULL,
        value	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(id AUTOINCREMENT) ON CONFLICT REPLACE,
        FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
    );""")

    for d in exp:
        d["item_id"] = d["game_id"]

    # add expertise again
    cur.executemany(
        "INSERT INTO expertise (id, item_id, user_id, value) VALUES (:id, :item_id, :user_id, :value);",
        exp
    )

    cur.execute("""CREATE TABLE datatags (
        id INTEGER PRIMARY KEY,
        item_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users (id),
        UNIQUE (item_id, tag_id, created_by)
    );""")

    for d in dts:
        d["item_id"] = d["game_id"]

    # add datatags again
    cur.executemany(
        "INSERT INTO datatags (id, item_id, tag_id, code_id, created, created_by) VALUES (:id, :item_id, :tag_id, :code_id, :created, :created_by);",
        dts
    )

    cur.execute("""CREATE TABLE evidence (
        id INTEGER PRIMARY KEY,
        item_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        tag_id INTEGER,
        description TEXT NOT NULL,
        filepath TEXT,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users (id)
    );""")

    for d in ev:
        d["item_id"] = d["game_id"]

    # add evidence again
    cur.executemany(
        "INSERT INTO evidence (id, item_id, tag_id, code_id, created, created_by, description, filepath) VALUES (:id, :item_id, :tag_id, :code_id, :created, :created_by, :description, :filepath);",
        ev
    )

    cur.execute("""CREATE TABLE meta_groups (
        id	INTEGER PRIMARY KEY,
        name	TEXT NOT NULL,
        item_id	INTEGER NOT NULL,
        code_id	INTEGER NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        FOREIGN KEY(code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE
    );""")

    for d in ext_g:
        d["item_id"] = d["game_id"]

    # add externalization groups again
    cur.executemany(
        "INSERT INTO evidence (id, name, item_id, code_id, created, created_by) VALUES (:id, :name, :item_id, :code_id, :created, :created_by);",
        ext_g
    )

    # --------------------------
    # add new tables
    # --------------------------

    # additional (meta) data table for games dataset
    cur.execute("""CREATE TABLE games_data (
        id	INTEGER PRIMARY KEY,
        item_id	INTEGER,
        year	INTEGER NOT NULL,
        steam_id	INTEGER,
	    FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE
    );""")

    rows = []
    for d in games:
        steam_id = get_steam_id(d["url"])
        rows.append({ "item_id": d["id"], "year": d["year"], "steam_id": steam_id })

    cur.executemany(
        "INSERT INTO games_data (item_id, year, steam_id) VALUES (:item_id, :year, :steam_id);",
        rows
    )

def downgrade(connection):
    # add your downgrade step here
    pass
