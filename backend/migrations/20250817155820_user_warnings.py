"""
This module contains a Caribou migration.

Migration Name: user_warnings
Migration Version: 20250817155820
"""

TBL_USERS_PRJ = "project_users"

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}


def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    users = cur.execute(f"SELECT * FROM {TBL_USERS_PRJ};").fetchall()

    cur.execute(f"DELETE FROM {TBL_USERS_PRJ}")
    cur.execute(f"DROP TABLE {TBL_USERS_PRJ}")

    # update project users table
    cur.execute(
        f"""CREATE TABLE {TBL_USERS_PRJ} (
            id	INTEGER PRIMARY KEY,
            user_id  INTEGER NOT NULL,
            dataset_id	INTEGER NOT NULL,
            enable_warnings INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            UNIQUE (user_id, dataset_id)
        );"""
    )

    for u in users:
        u["enable_warnings"] = 0

    cur.executemany(
        f"INSERT INTO {TBL_USERS_PRJ} (id, user_id, dataset_id, enable_warnings) VALUES " +
        "(:id, :user_id, :dataset_id, :enable_warnings)",
        users
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    users = cur.execute(f"SELECT * FROM {TBL_USERS_PRJ};").fetchall()

    cur.execute(f"DELETE FROM {TBL_USERS_PRJ}")
    cur.execute(f"DROP TABLE {TBL_USERS_PRJ}")

    # update project users table
    cur.execute(
        f"""CREATE TABLE {TBL_USERS_PRJ} (
            id	INTEGER PRIMARY KEY,
            user_id  INTEGER NOT NULL,
            dataset_id	INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            UNIQUE (user_id, dataset_id)
        );"""
    )

    for u in users:
        u["enable_warnings"] = 0

    cur.executemany(
        f"INSERT INTO {TBL_USERS_PRJ} (id, user_id, dataset_id) VALUES " +
        "(:id, :user_id, :dataset_id)",
        users
    )

    connection.commit()
