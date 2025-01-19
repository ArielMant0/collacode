"""
This module contains a Caribou migration.

Migration Name: code_constraint
Migration Version: 20250119160335
"""
def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all codes
    codes = cur.execute("SELECT * FROM codes;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM codes;")
    cur.execute("DROP TABLE codes;")

    # create new users table
    cur.execute("""CREATE TABLE codes (
        id INTEGER PRIMARY KEY,
        dataset_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users (id),
        CONSTRAINT uc_combi UNIQUE (name, dataset_id)
    );""")

    cur.executemany(
        "INSERT INTO codes (id, dataset_id, name, description, created, created_by) VALUES (:id, :dataset_id, :name, :description, :created, :created_by);",
        codes
    )

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

        # get all codes
    codes = cur.execute("SELECT * FROM codes;").fetchall()

    # delete codes table
    cur.execute("DELETE FROM codes;")
    cur.execute("DROP TABLE codes;")

    # create new users table
    cur.execute("""CREATE TABLE codes (
        id INTEGER PRIMARY KEY,
        dataset_id INTEGER NOT NULL,
        name TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL,
        created INTEGER NOT NULL,
        created_by INTEGER NOT NULL,
        FOREIGN KEY (dataset_id) REFERENCES datasets (id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users (id)
    );""")

    cur.executemany(
        "INSERT codes (id, dataset_id, name, description, created, created_by) VALUES (:id, :dataset_id, :name, :description, :created, :created_by);",
        codes
    )

    connection.commit()
