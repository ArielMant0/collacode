"""
This module contains a Caribou migration.

Migration Name: item_notes
Migration Version: 20260830100540
"""

TBL_ITEM_NOTES = "item_notes"

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):

    connection.row_factory = dict_factory
    cur = connection.cursor()

    # add new item notes table
    cur.execute(
        f"""CREATE TABLE {TBL_ITEM_NOTES} (
            id	INTEGER PRIMARY KEY,
            dataset_id  INTEGER NOT NULL,
            item_id  INTEGER NOT NULL,
            user_id  INTEGER NOT NULL,
            created  INTEGER NOT NULL,
            updated  INTEGER NOT NULL,
            text TEXT DEFAULT NULL,
            FOREIGN KEY(dataset_id) REFERENCES datasets(id) ON DELETE CASCADE,
            FOREIGN KEY(item_id) REFERENCES items(id) ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE (user_id, item_id)
        );"""
    )

    connection.commit()


def downgrade(connection):
    connection.row_factory = dict_factory
    cur = connection.cursor()

    cur.execute(f"DELETE FROM {TBL_ITEM_NOTES}")
    cur.execute(f"DROP TABLE {TBL_ITEM_NOTES}")

    connection.commit()
