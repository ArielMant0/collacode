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

    last_idx = url.find("/", app_idx + 4)
    if last_idx < 0:
        return None

    return int(url[app_idx + 4 : last_idx])


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

    ext_agreements = cur.execute("SELECT * FROM ext_agreements;").fetchall()
    ext_categories = cur.execute("SELECT * FROM ext_categories;").fetchall()
    ext_tag = cur.execute("SELECT * FROM ext_tag_connections;").fetchall()
    ext_cat = cur.execute("SELECT * FROM ext_cat_connections;").fetchall()
    ext_ev = cur.execute("SELECT * FROM ext_ev_connections;").fetchall()

    cur.execute("DELETE FROM datasets;")
    cur.execute("DELETE FROM games;")
    cur.execute("DELETE FROM game_expertise;")
    cur.execute("DELETE FROM datatags;")
    cur.execute("DELETE FROM evidence;")
    cur.execute("DELETE FROM ext_groups;")
    cur.execute("DELETE FROM externalizations;")
    cur.execute("DELETE FROM ext_agreements;")
    cur.execute("DELETE FROM ext_categories;")
    cur.execute("DELETE FROM ext_tag_connections;")
    cur.execute("DELETE FROM ext_cat_connections;")
    cur.execute("DELETE FROM ext_ev_connections;")

    cur.execute("DROP TABLE datasets;")
    cur.execute("DROP TABLE games;")
    cur.execute("DROP TABLE game_expertise;")
    cur.execute("DROP TABLE datatags;")
    cur.execute("DROP TABLE evidence;")
    cur.execute("DROP TABLE ext_groups;")
    cur.execute("DROP TABLE externalizations;")
    cur.execute("DROP TABLE ext_agreements;")
    cur.execute("DROP TABLE ext_categories;")
    cur.execute("DROP TABLE ext_tag_connections;")
    cur.execute("DROP TABLE ext_cat_connections;")
    cur.execute("DROP TABLE ext_ev_connections;")

    # --------------------------
    # re-add datasets table
    # --------------------------

    cur.execute(
        """CREATE TABLE datasets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        meta_scheme TEXT,
        meta_table TEXT,
        description TEXT);"""
    )

    for d in ds:
        if "meta_scheme" not in d:
            d["meta_scheme"] = f"scheme_{d['id']}.json"
        if "meta_table" not in d:
            d["meta_table"] = "games_data"
        if "description" not in d:
            d["description"] = None

    # add datasets again
    cur.executemany(
        "INSERT INTO datasets (id, name, meta_scheme, meta_table, description) VALUES (:id, :name, :meta_scheme, :meta_table, :description);",
        ds,
    )
    print(f"added {cur.rowcount} datasets")

    # --------------------------
    # re-add all other tables
    # --------------------------

    cur.execute(
        """CREATE TABLE items (
        id INTEGER PRIMARY KEY,
        dataset_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        url TEXT,
        teaser TEXT,
        FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE);"""
    )

    for d in games:
        if "description" not in d:
            d["description"] = None

    # add games again
    cur.executemany(
        "INSERT INTO items (id, name, dataset_id, description, url, teaser) VALUES (:id, :name, :dataset_id, :description, :url, :teaser);",
        games,
    )
    print(f"added {cur.rowcount} games")

    cur.execute(
        """CREATE TABLE expertise (
        id	INTEGER UNIQUE NOT NULL,
        item_id	INTEGER NOT NULL,
        user_id	INTEGER NOT NULL,
        value	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(id AUTOINCREMENT) ON CONFLICT REPLACE,
        FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in exp:
        d["item_id"] = d["game_id"]

    # add expertise again
    cur.executemany(
        "INSERT INTO expertise (id, item_id, user_id, value) VALUES (:id, :item_id, :user_id, :value);",
        exp,
    )
    print(f"added {cur.rowcount} expertise ratings")

    cur.execute(
        """CREATE TABLE datatags (
        id INTEGER PRIMARY KEY,
        item_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (item_id) REFERENCES items (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE (item_id, tag_id, created_by));"""
    )

    for d in dts:
        d["item_id"] = d["game_id"]

    # add datatags again
    cur.executemany(
        "INSERT INTO datatags (id, item_id, tag_id, code_id, created, created_by) VALUES (:id, :item_id, :tag_id, :code_id, :created, :created_by);",
        dts,
    )
    print(f"added {cur.rowcount} datatags")

    cur.execute(
        """CREATE TABLE evidence (
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
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in ev:
        d["item_id"] = d["game_id"]

    # add evidence again
    cur.executemany(
        "INSERT INTO evidence (id, item_id, tag_id, code_id, created, created_by, description, filepath) VALUES (:id, :item_id, :tag_id, :code_id, :created, :created_by, :description, :filepath);",
        ev,
    )
    print(f"added {cur.rowcount} evidence pieces")

    cur.execute(
        """CREATE TABLE meta_groups (
        id	INTEGER PRIMARY KEY,
        name	TEXT NOT NULL,
        item_id	INTEGER NOT NULL,
        code_id	INTEGER NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        FOREIGN KEY(code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE);"""
    )

    for d in ext_g:
        d["item_id"] = d["game_id"]

    # add externalization groups again
    cur.executemany(
        "INSERT INTO meta_groups (id, name, item_id, code_id, created, created_by) VALUES (:id, :name, :item_id, :code_id, :created, :created_by);",
        ext_g,
    )
    print(f"added {cur.rowcount} externalization groups")

    cur.execute(
        """CREATE TABLE meta_items (
        id	INTEGER PRIMARY KEY,
        group_id	INTEGER NOT NULL,
        name	TEXT NOT NULL,
        cluster	TEXT NOT NULL DEFAULT "misc",
        description	TEXT NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        FOREIGN KEY(group_id) REFERENCES meta_groups (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    # add externalizations again
    cur.executemany(
        "INSERT INTO meta_items (id, name, group_id, cluster, description, created, created_by) VALUES (:id, :name, :group_id, :cluster, :description, :created, :created_by);",
        ext,
    )
    print(f"added {cur.rowcount} externalizations")

    cur.execute(
        """CREATE TABLE meta_categories (
        id	INTEGER PRIMARY KEY,
        parent	INTEGER,
        description	TEXT NOT NULL,
        name	TEXT NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        dataset_id	INTEGER NOT NULL,
        code_id	INTEGER NOT NULL,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
        FOREIGN KEY(parent) REFERENCES meta_categories (id) ON DELETE SET NULL);"""
    )

    for d in ext_categories:
        d["dataset_id"] = d["dataset"]

    # add externalization categories again
    cur.executemany(
        "INSERT INTO meta_categories (id, parent, description, name, description, created, created_by, dataset_id, code_id) VALUES (:id, :parent, :description, :name, :description, :created, :created_by, :dataset_id, :code_id);",
        ext_categories,
    )
    print(f"added {cur.rowcount} externalization categories")

    cur.execute(
        """CREATE TABLE meta_tag_connections (
        id	INTEGER PRIMARY KEY,
        meta_id	INTEGER NOT NULL,
        tag_id	INTEGER NOT NULL,
        FOREIGN KEY(meta_id) REFERENCES meta_items (id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE);"""
    )

    for d in ext_tag:
        d["meta_id"] = d["ext_id"]

    # add externalization tag connections again
    cur.executemany(
        "INSERT INTO meta_tag_connections (id, meta_id, tag_id) VALUES (:id, :meta_id, :tag_id);",
        ext_tag,
    )
    print(f"added {cur.rowcount} externalization tag connections")

    cur.execute(
        """CREATE TABLE meta_cat_connections (
        id	INTEGER PRIMARY KEY,
        meta_id	INTEGER NOT NULL,
        cat_id	INTEGER NOT NULL,
        FOREIGN KEY(meta_id) REFERENCES meta_items (id) ON DELETE CASCADE,
        FOREIGN KEY(cat_id) REFERENCES meta_categories (id) ON DELETE CASCADE);"""
    )

    for d in ext_cat:
        d["meta_id"] = d["ext_id"]

    # add externalization category connections again
    cur.executemany(
        "INSERT INTO meta_cat_connections (id, meta_id, cat_id) VALUES (:id, :meta_id, :cat_id);",
        ext_cat,
    )
    print(f"added {cur.rowcount} externalization category connections")

    cur.execute(
        """CREATE TABLE meta_ev_connections (
        id	INTEGER PRIMARY KEY,
        meta_id	INTEGER NOT NULL,
        ev_id	INTEGER NOT NULL,
        FOREIGN KEY(meta_id) REFERENCES meta_items (id) ON DELETE CASCADE,
        FOREIGN KEY(ev_id) REFERENCES evidence (id) ON DELETE CASCADE);"""
    )

    for d in ext_ev:
        d["meta_id"] = d["ext_id"]

    # add externalization evidence connections again
    cur.executemany(
        "INSERT INTO meta_ev_connections (id, meta_id, ev_id) VALUES (:id, :meta_id, :ev_id);",
        ext_ev,
    )
    print(f"added {cur.rowcount} externalization evidence connections")

    cur.execute(
        """CREATE TABLE meta_agreements (
        id	INTEGER PRIMARY KEY,
        meta_id	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        value	INTEGER NOT NULL,
        FOREIGN KEY(meta_id) REFERENCES meta_items (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in ext_agreements:
        d["meta_id"] = d["ext_id"]

    # add externalization agreements again
    cur.executemany(
        "INSERT INTO meta_agreements (id, meta_id, created_by, value) VALUES (:id, :meta_id, :created_by, :value);",
        ext_agreements,
    )
    print(f"added {cur.rowcount} externalization agreements")

    # --------------------------
    # add new tables
    # --------------------------

    # additional (meta) data table for games dataset
    cur.execute(
        """CREATE TABLE games_data (
        id INTEGER PRIMARY KEY,
        item_id	INTEGER,
        year INTEGER NOT NULL,
        steam_id INTEGER,
        FOREIGN KEY(item_id) REFERENCES items (id) ON DELETE CASCADE);"""
    )

    rows = []
    for d in games:
        steam_id = get_steam_id(d["url"])
        rows.append({"item_id": d["id"], "year": d["year"], "steam_id": steam_id})

    cur.executemany(
        "INSERT INTO games_data (item_id, year, steam_id) VALUES (:item_id, :year, :steam_id);",
        rows,
    )
    print(f"added meta data for {cur.rowcount} games")

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    ds = cur.execute("SELECT * FROM datasets;").fetchall()
    games = cur.execute("SELECT * FROM items;").fetchall()
    meta_tables = {}
    for d in games:
        meta_tables[d] = cur.execute(f"SELECT * FROM {d['meta_table']};").fetchall()

    exp = cur.execute("SELECT * FROM expertise;").fetchall()
    dts = cur.execute("SELECT * FROM datatags;").fetchall()
    ev = cur.execute("SELECT * FROM evidence;").fetchall()
    ext_g = cur.execute("SELECT * FROM meta_groups;").fetchall()
    ext = cur.execute("SELECT * FROM meta_items;").fetchall()

    ext_agreements = cur.execute("SELECT * FROM meta_agreements;").fetchall()
    ext_categories = cur.execute("SELECT * FROM meta_categories;").fetchall()
    ext_tag = cur.execute("SELECT * FROM meta_tag_connections;").fetchall()
    ext_cat = cur.execute("SELECT * FROM meta_cat_connections;").fetchall()
    ext_ev = cur.execute("SELECT * FROM meta_ev_connections;").fetchall()

    cur.execute("DELETE FROM datasets;")
    cur.execute("DELETE FROM items;")
    cur.execute("DELETE FROM expertise;")
    cur.execute("DELETE FROM datatags;")
    cur.execute("DELETE FROM evidence;")
    cur.execute("DELETE FROM meta_groups;")
    cur.execute("DELETE FROM meta_items;")
    cur.execute("DELETE FROM meta_agreements;")
    cur.execute("DELETE FROM meta_categories;")
    cur.execute("DELETE FROM meta_tag_connections;")
    cur.execute("DELETE FROM meta_cat_connections;")
    cur.execute("DELETE FROM meta_ev_connections;")

    cur.execute("DROP TABLE datasets;")
    cur.execute("DROP TABLE items;")
    cur.execute("DROP TABLE expertise;")
    cur.execute("DROP TABLE datatags;")
    cur.execute("DROP TABLE evidence;")
    cur.execute("DROP TABLE meta_groups;")
    cur.execute("DROP TABLE meta_items;")
    cur.execute("DROP TABLE meta_agreements;")
    cur.execute("DROP TABLE meta_categories;")
    cur.execute("DROP TABLE meta_tag_connections;")
    cur.execute("DROP TABLE meta_cat_connections;")
    cur.execute("DROP TABLE meta_ev_connections;")

    # --------------------------
    # re-add datasets table
    # --------------------------

    cur.execute(
        """CREATE TABLE datasets (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL UNIQUE,
        description TEXT);"""
    )

    for d in ds:
        if "description" not in d:
            d["description"] = None

    # add datasets again
    cur.executemany(
        "INSERT INTO datasets (id, name, description) VALUES (:id, :name, :description);",
        ds,
    )
    print(f"added {cur.rowcount} datasets")

    # --------------------------
    # re-add all other tables
    # --------------------------

    cur.execute(
        """CREATE TABLE games (
        id INTEGER PRIMARY KEY,
        dataset_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        year INTEGER,
        url TEXT,
        teaser TEXT,
        FOREIGN KEY(dataset_id) REFERENCES datasets (id) ON DELETE CASCADE);"""
    )

    for d in games:
        if "description" not in d:
            d["description"] = None

        table = meta_tables[d["dataset_id"]]
        other = [t for t in table if t["item_id"] == d["id"]][0]
        d["year"] = other["year"]

    # add games again
    cur.executemany(
        "INSERT INTO items (id, name, dataset_id, description, url, teaser, year) VALUES (:id, :name, :dataset_id, :description, :url, :teaser, :year);",
        games,
    )
    print(f"added {cur.rowcount} games")

    cur.execute(
        """CREATE TABLE game_expertise (
        id	INTEGER UNIQUE NOT NULL,
        game_id	INTEGER NOT NULL,
        user_id	INTEGER NOT NULL,
        value	INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(id AUTOINCREMENT) ON CONFLICT REPLACE,
        FOREIGN KEY(game_id) REFERENCES games (id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in exp:
        d["game_id"] = d["item_id"]

    # add expertise again
    cur.executemany(
        "INSERT INTO expertise (id, game_id, user_id, value) VALUES (:id, :game_id, :user_id, :value);",
        exp,
    )
    print(f"added {cur.rowcount} expertise ratings")

    cur.execute(
        """CREATE TABLE datatags (
        id INTEGER PRIMARY KEY,
        game_id INTEGER NOT NULL,
        tag_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE,
        UNIQUE (game_id, tag_id, created_by));"""
    )

    for d in dts:
        d["game_id"] = d["item_id"]

    # add datatags again
    cur.executemany(
        "INSERT INTO datatags (id, game_id, tag_id, code_id, created, created_by) VALUES (:id, :game_id, :tag_id, :code_id, :created, :created_by);",
        dts,
    )
    print(f"added {cur.rowcount} datatags")

    cur.execute(
        """CREATE TABLE evidence (
        id INTEGER PRIMARY KEY,
        game_id INTEGER NOT NULL,
        code_id INTEGER NOT NULL,
        tag_id INTEGER,
        description TEXT NOT NULL,
        filepath TEXT,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (game_id) REFERENCES games (id) ON DELETE CASCADE,
        FOREIGN KEY (code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in ev:
        d["game_id"] = d["item_id"]

    # add evidence again
    cur.executemany(
        "INSERT INTO evidence (id, game_id, tag_id, code_id, created, created_by, description, filepath) VALUES (:id, :game_id, :tag_id, :code_id, :created, :created_by, :description, :filepath);",
        ev,
    )
    print(f"added {cur.rowcount} evidence pieces")

    cur.execute(
        """CREATE TABLE ext_groups (
        id	INTEGER PRIMARY KEY,
        name	TEXT NOT NULL,
        game_id	INTEGER NOT NULL,
        code_id	INTEGER NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        FOREIGN KEY(code_id) REFERENCES codes (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(game_id) REFERENCES games (id) ON DELETE CASCADE);"""
    )

    for d in ext_g:
        d["game_id"] = d["item_id"]

    # add externalization groups again
    cur.executemany(
        "INSERT INTO ext_groups (id, name, game_id, code_id, created, created_by) VALUES (:id, :name, :game_id, :code_id, :created, :created_by);",
        ext_g,
    )
    print(f"added {cur.rowcount} externalization groups")

    cur.execute(
        """CREATE TABLE externalizations (
        id	INTEGER PRIMARY KEY,
        group_id	INTEGER NOT NULL,
        name	TEXT NOT NULL,
        cluster	TEXT NOT NULL DEFAULT "misc",
        description	TEXT NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        FOREIGN KEY(group_id) REFERENCES meta_groups (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    # add externalizations again
    cur.executemany(
        "INSERT INTO externalizations (id, name, group_id, cluster, description, created, created_by) VALUES (:id, :name, :group_id, :cluster, :description, :created, :created_by);",
        ext,
    )
    print(f"added {cur.rowcount} externalizations")

    cur.execute(
        """CREATE TABLE ext_categories (
        id	INTEGER PRIMARY KEY,
        parent	INTEGER,
        description	TEXT NOT NULL,
        name	TEXT NOT NULL,
        created	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        dataset	INTEGER NOT NULL,
        code_id	INTEGER NOT NULL,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE,
        FOREIGN KEY(dataset) REFERENCES datasets (id) ON DELETE CASCADE,
        FOREIGN KEY(parent) REFERENCES ext_categories (id) ON DELETE SET NULL);"""
    )

    for d in ext_categories:
        d["dataset"] = d["dataset_id"]

    # add externalization categories again
    cur.executemany(
        "INSERT INTO ext_categories (id, parent, description, name, description, created, created_by, dataset, code_id) VALUES (:id, :parent, :description, :name, :description, :created, :created_by, :dataset, :code_id);",
        ext_categories,
    )
    print(f"added {cur.rowcount} externalization categories")

    cur.execute(
        """CREATE TABLE ext_tag_connections (
        id	INTEGER PRIMARY KEY,
        ext_id	INTEGER NOT NULL,
        tag_id	INTEGER NOT NULL,
        FOREIGN KEY(ext_id) REFERENCES externalizations (id) ON DELETE CASCADE,
        FOREIGN KEY(tag_id) REFERENCES tags (id) ON DELETE CASCADE);"""
    )

    for d in ext_tag:
        d["ext_id"] = d["meta_id"]

    # add externalization tag connections again
    cur.executemany(
        "INSERT INTO ext_tag_connections (id, ext_id, tag_id) VALUES (:id, :ext_id, :tag_id);",
        ext_tag,
    )
    print(f"added {cur.rowcount} externalization tag connections")

    cur.execute(
        """CREATE TABLE ext_cat_connections (
        id	INTEGER PRIMARY KEY,
        ext_id	INTEGER NOT NULL,
        cat_id	INTEGER NOT NULL,
        FOREIGN KEY(ext_id) REFERENCES externalizations (id) ON DELETE CASCADE,
        FOREIGN KEY(cat_id) REFERENCES ext_categories (id) ON DELETE CASCADE);"""
    )

    for d in ext_cat:
        d["ext_id"] = d["meta_id"]

    # add externalization category connections again
    cur.executemany(
        "INSERT INTO ext_cat_connections (id, ext_id, cat_id) VALUES (:id, :ext_id, :cat_id);",
        ext_cat,
    )
    print(f"added {cur.rowcount} externalization category connections")

    cur.execute(
        """CREATE TABLE ext_ev_connections (
        id	INTEGER PRIMARY KEY,
        ext_id	INTEGER NOT NULL,
        ev_id	INTEGER NOT NULL,
        FOREIGN KEY(ext_id) REFERENCES externalizations (id) ON DELETE CASCADE,
        FOREIGN KEY(ev_id) REFERENCES evidence (id) ON DELETE CASCADE);"""
    )

    for d in ext_ev:
        d["ext_id"] = d["meta_id"]

    # add externalization evidence connections again
    cur.executemany(
        "INSERT INTO ext_ev_connections (id, ext_id, ev_id) VALUES (:id, :ext_id, :ev_id);",
        ext_ev,
    )
    print(f"added {cur.rowcount} externalization evidence connections")

    cur.execute(
        """CREATE TABLE ext_agreements (
        id	INTEGER PRIMARY KEY,
        ext_id	INTEGER NOT NULL,
        created_by	INTEGER NOT NULL,
        value	INTEGER NOT NULL,
        FOREIGN KEY(ext_id) REFERENCES externalizations (id) ON DELETE CASCADE,
        FOREIGN KEY(created_by) REFERENCES users (id) ON DELETE CASCADE);"""
    )

    for d in ext_agreements:
        d["ext_id"] = d["meta_id"]

    # add externalization agreements again
    cur.executemany(
        "INSERT INTO ext_agreements (id, ext_id, created_by, value) VALUES (:id, :ext_id, :created_by, :value);",
        ext_agreements,
    )
    print(f"added {cur.rowcount} externalization agreements")

    # --------------------------
    # remove added tables
    # --------------------------

    # additional (meta) data table for games dataset
    for k in meta_tables.keys():
        cur.execute(f"DELETE FROM {k};")
        cur.execute(f"DROP TABLE {k};")

    print(f"removed {len(meta_tables.keys())} meta data tables")

    connection.commit()
