import os
import sqlite3
import unittest

from pathlib import Path

import config
import app.db_wrapper as dbw

from table_constants import (
    TBL_DATATAGS,
    TBL_EVIDENCE,
    TBL_ITEMS,
    TBL_TAGS,
)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "data", "data-test.db"
).resolve()
EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", config.EVIDENCE_PATH
).resolve()

class TagTestCase(unittest.TestCase):

    def setUp(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.dataset_id = 1
        self.code_id = 1
        self.user_id = 1


    def tearDown(self):
        self.db.rollback()


    def test_add_tag(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()
        tag = {
            "name": "test tag add",
            "description": "no desc",
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        dbw.add_tags(cur, [tag])

        res = cur.execute(
            f"SELECT * FROM {TBL_TAGS} WHERE name = ? AND code_id =? AND created_by = ?",
            (tag["name"], tag["code_id"], tag["created_by"])
        ).fetchone()

        self.assertIsNotNone(res, 'tag not added to database')
        self.assertEqual(tag["name"], res.name, 'tag names are not equal')
        self.assertEqual(tag["description"], res.description, 'tag descriptions are not equal')
        self.assertEqual(tag["code_id"], res.code_id, 'tag code ids are not equal')
        self.assertEqual(tag["created_by"], res.created_by, 'tag users are not equal')
        self.assertEqual(tag["created"], res.created, 'tag times are not equal')
        self.db.rollback()


    def test_delete_tag_without_datatags(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()
        tag = {
            "name": "test tag delete",
            "description": "no desc",
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        tag["id"] = dbw.add_tag_return_id(cur, tag)
        self.assertIsNotNone(tag["id"], 'tag not added to database')

        dbw.delete_tags(cur, [tag["id"]], EVIDENCE_PATH)

        res = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?", (tag["id"],)).fetchone()
        self.assertIsNone(res, 'tag not deleted from database')

        dts = cur.execute(f"SELECT * FROM {TBL_DATATAGS} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(dts), 0, 'datatags were not deleted')

        evs = cur.execute(f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(evs), 0, 'evidence was not deleted')


    def test_delete_tag_with_datatags(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()
        tag = {
            "name": "test tag with datatags",
            "description": "no desc",
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        tag["id"] = dbw.add_tag_return_id(cur, tag)
        self.assertIsNotNone(tag["id"], 'tag not added to database')

        item = cur.execute(
            f"SELECT id FROM {TBL_ITEMS} WHERE dataset_id = ? LIMIT 1;",
            (self.dataset_id,)
        ).fetchone()

        self.assertIsNotNone(item, 'no item in database')

        datatag = {
            "tag_id": tag["id"],
            "item_id": item.id,
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }

        dbw.add_datatags(cur, [datatag])
        dtsBefore = cur.execute(
            f"SELECT * FROM {TBL_DATATAGS} WHERE tag_id = ?",
            (tag["id"],)
        ).fetchall()
        self.assertEqual(len(dtsBefore), 1, f'datatags were not added')

        dbw.delete_tags(cur, [tag["id"]], EVIDENCE_PATH)

        res = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?", (tag["id"],)).fetchone()
        self.assertIsNone(res, 'tag not deleted from database')

        dts = cur.execute(f"SELECT * FROM {TBL_DATATAGS} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(dts), 0, 'datatags were not deleted')

        evs = cur.execute(f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(evs), 0, 'evidence was not deleted')


    def test_delete_tag_with_evidence(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()
        tag = {
            "name": "test tag with evidence",
            "description": "no desc",
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        tag["id"] = dbw.add_tag_return_id(cur, tag)
        self.assertIsNotNone(tag["id"], 'tag not added to database')

        item = cur.execute(
            f"SELECT id FROM {TBL_ITEMS} WHERE dataset_id = ? LIMIT 1;",
            (self.dataset_id,)
        ).fetchone()

        self.assertIsNotNone(item, 'no item in database')

        evidence = {
            "description": "this is a test evidence",
            "tag_id": tag["id"],
            "type": 1,
            "item_id": item.id,
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }

        dbw.add_evidence(cur, [evidence])
        evsBefore = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ?",
            (tag["id"],)
        ).fetchall()
        self.assertEqual(len(evsBefore), 1, f'evidence was not added')

        dbw.delete_tags(cur, [tag["id"]], EVIDENCE_PATH)

        res = cur.execute(f"SELECT * FROM {TBL_TAGS} WHERE id = ?", (tag["id"],)).fetchone()
        self.assertIsNone(res, 'tag not deleted from database')

        dts = cur.execute(f"SELECT * FROM {TBL_DATATAGS} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(dts), 0, 'datatags were not deleted')

        evs = cur.execute(f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ?",(tag["id"],)).fetchall()
        self.assertEqual(len(evs), 0, 'evidence was not deleted')


if __name__ == '__main__':
    unittest.main()
