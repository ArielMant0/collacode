"""
This module contains a Caribou migration.

Migration Name: tag_assig_rework
Migration Version: 20241223131404
"""
from datetime import datetime, timezone

def dict_factory(cursor, row):
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def upgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all transitions
    trans = cur.execute("SELECT * FROM code_transitions;").fetchall()

    taPerTrans = []
    for t in trans:
        # get all tag assignments for this transition
        taPerTrans.append(cur.execute(
            "SELECT * FROM tag_assignments WHERE old_code = ? AND new_code = ?;",
            (t["old_code"], t["new_code"])
        ).fetchall())

    # delete tag assignments table
    cur.execute("DELETE FROM tag_assignments;")
    cur.execute("DROP TABLE tag_assignments;")

    # create tag assignments table
    cur.execute("""CREATE TABLE IF NOT EXISTS "tag_assignments" (
        "id"	integer,
        "old_code"	integer NOT NULL,
        "new_code"	integer NOT NULL,
        "old_tag"	integer NOT NULL,
        "new_tag"	integer NOT NULL,
        "description"	text,
        "created"	integer NOT NULL,
        PRIMARY KEY("id"),
        UNIQUE("old_code","new_code","old_tag","new_tag"),
        CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_new_tag" FOREIGN KEY("new_tag") REFERENCES "tags"("id") ON DELETE SET NULL,
        CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_old_tag" FOREIGN KEY("old_tag") REFERENCES "tags"("id") ON DELETE SET NULL
    );""")

    # add tag assignments
    for list in taPerTrans:

        f = [t for t in list if t["old_tag"] is not None and t["new_tag"] is not None]
        cur.executemany("INSERT INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) " +
            "VALUES (:id, :old_code, :new_code, :old_tag, :new_tag, :description, :created);",
            f
        )
        print(f"added {len(f)} existing tag assignments")

    connection.commit()

def downgrade(connection):
    # add your upgrade step here
    connection.row_factory = dict_factory
    cur = connection.cursor()

    # get all transitions
    trans = cur.execute("SELECT * FROM code_transitions;").fetchall()

    taPerTrans = []
    for t in trans:
        # get all tag assignments for this transition
        taPerTrans.append(cur.execute(
            "SELECT * FROM tag_assignments WHERE old_code = ? AND new_code = ?;",
            (t["old_code"], t["new_code"])
        ).fetchall())

    # delete tag assignments table
    cur.execute("DELETE FROM tag_assignments;")
    cur.execute("DROP TABLE tag_assignments;")

    # create tag assignments table
    cur.execute("""CREATE TABLE IF NOT EXISTS "tag_assignments" (
        "id"	integer,
        "old_code"	integer NOT NULL,
        "new_code"	integer NOT NULL,
        "old_tag"	integer NOT NULL,
        "new_tag"	integer,
        "description"	text,
        "created"	integer NOT NULL,
        PRIMARY KEY("id"),
        UNIQUE("old_code","new_code","old_tag","new_tag"),
        CONSTRAINT "fk_new_code" FOREIGN KEY("new_code") REFERENCES "codes"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_new_tag" FOREIGN KEY("new_tag") REFERENCES "tags"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_old_code" FOREIGN KEY("old_code") REFERENCES "codes"("id") ON DELETE CASCADE,
        CONSTRAINT "fk_old_tag" FOREIGN KEY("old_tag") REFERENCES "tags"("id") ON DELETE CASCADE
    );""")

    # add tag assignments
    for list in taPerTrans:
        f = [t for t in list if t["old_tag"] is not None]

        cur.executemany("INSERT INTO tag_assignments (id, old_code, new_code, old_tag, new_tag, description, created) " +
            "VALUES (:id, :old_code, :new_code, :old_tag, :new_tag, :description, :created);",
            f
        )

    cur.execute("DELETE FROM tag_assignments WHERE old_tag = NULL AND new_tag = NULL;")
    connection.commit()
