import os
import sqlite3
import unittest

from pathlib import Path

import config
import app.db_wrapper as dbw

from table_constants import (
    TBL_DATATAGS,
    TBL_ITEMS,
    TBL_TAGS,
)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "data", "data-test.db"
).resolve()
EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", config.EVIDENCE_PATH
).resolve()

class DatatagsTestCase(unittest.TestCase):

    def setUp(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.dataset_id = 1
        self.code_id = 1
        self.user_id = 1

        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        # get an item
        self.item = cur.execute(
            f"SELECT DISTINCT i.* FROM {TBL_ITEMS} i WHERE i.dataset_id = ? LIMIT 1;",
            (self.dataset_id,)
        ).fetchone()
        self.item_id = self.item.id

        # get 3 tags the item does not have
        tags = cur.execute(
            f"""SELECT DISTINCT t.id FROM {TBL_TAGS} t
            JOIN {TBL_DATATAGS} dt ON dt.tag_id = t.id
            JOIN {TBL_ITEMS} i ON dt.item_id = i.id
            WHERE i.id != ? AND t.code_id = ? LIMIT 3;""",
            (self.item.id, self.item.code_id)
        ).fetchall()
        self.tag_ids = [t.id for t in tags]


    def tearDown(self):
        self.db.rollback()


    def test_add_delete_datatag(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()
        dt = {
            "item_id": self.item_id,
            "tag_id": self.tag_ids[0],
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        dbw.add_datatags(cur, [dt])

        res = cur.execute(
            f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND tag_id = ? AND created_by = ?",
            (self.item_id, self.tag_ids[0], self.user_id)
        ).fetchall()

        self.assertEqual(len(res), 1, 'datatag not added to database')

        dbw.delete_datatags(cur, [d.id for d in res])
        dts = cur.execute(
            f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND tag_id = ? AND created_by = ?",
            (self.item_id, self.tag_ids[0], self.user_id)
        ).fetchall()

        self.assertEqual(len(dts), 0, 'datatags were not deleted')


    def test_update_item_datatags(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        dts1 = {
            "item_id": self.item_id,
            "tag_id": self.tag_ids[0],
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        dts2 = {
            "item_id": self.item_id,
            "tag_id": self.tag_ids[1],
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        dbw.add_datatags(cur, [dts1, dts2])

        res1 = cur.execute(
            f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND tag_id = ? AND created_by = ?",
            (self.item_id, self.tag_ids[0], self.user_id)
        ).fetchall()
        self.assertEqual(len(res1), 1, 'datatag 1 not added to database')

        res2 = cur.execute(
            f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND tag_id = ? AND created_by = ?",
            (self.item_id, self.tag_ids[1], self.user_id)
        ).fetchall()
        self.assertEqual(len(res2), 1, 'datatag 2 not added to database')

        dts3 = {
            "item_id": self.item_id,
            "tag_id": self.tag_ids[2],
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        item = self.item._asdict()
        item["item_id"] = self.item_id
        item["user_id"] = self.user_id
        item["tags"] = [dts1, dts3]

        dbw.update_item_datatags(cur, item)

        dts = cur.execute(
            f"SELECT id FROM {TBL_DATATAGS} WHERE item_id = ? AND code_id = ? AND created_by = ?",
            (self.item_id, self.code_id, self.user_id)
        ).fetchall()

        self.assertEqual(len(dts), 2, 'datatags were not updated correctly')


if __name__ == '__main__':
    unittest.main()
