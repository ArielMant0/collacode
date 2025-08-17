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

class EvidenceTestCase(unittest.TestCase):

    def setUp(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.dataset_id = 1
        self.code_id = 1
        self.user_id = 1

        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        # get an item
        item = cur.execute(
            f"SELECT DISTINCT i.* FROM {TBL_ITEMS} i WHERE i.dataset_id = ? LIMIT 1;",
            (self.dataset_id,)
        ).fetchone()
        self.item_id = item.id

        # get 1 tag the item has
        tagHas = cur.execute(
            f"""SELECT DISTINCT t.id FROM {TBL_TAGS} t
            JOIN {TBL_DATATAGS} dt ON dt.tag_id = t.id
            JOIN {TBL_ITEMS} i ON dt.item_id = i.id
            WHERE i.id = ? AND t.code_id = ? LIMIT 1;""",
            (item.id, item.code_id)
        ).fetchone()
        self.tag_id_has = tagHas.id

        # get 1 tag the item does not have
        tagHasNot = cur.execute(
            f"""SELECT DISTINCT t.id FROM {TBL_TAGS} t
            JOIN {TBL_DATATAGS} dt ON dt.tag_id = t.id
            JOIN {TBL_ITEMS} i ON dt.item_id = i.id
            WHERE i.id != ? AND t.code_id = ? LIMIT 1;""",
            (item.id, item.code_id)
        ).fetchone()
        self.tag_id_has_not = tagHasNot.id


    def tearDown(self):
        self.db.rollback()


    def test_add_delete_evidence_positive(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        evsBefore = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 1",
            (self.tag_id_has,)
        ).fetchall()

        evidence = {
            "description": "this is a test evidence",
            "tag_id": self.tag_id_has,
            "type": 1,
            "item_id": self.item_id,
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        evid = dbw.add_evidence_return_id(cur, evidence)
        evsAfter = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 1",
            (self.tag_id_has,)
        ).fetchall()
        self.assertEqual(len(evsBefore)+1, len(evsAfter), f'evidence was not added')

        dbw.delete_evidence(cur, [evid], EVIDENCE_PATH)
        evsAfterDelete = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 1",
            (self.tag_id_has,)
        ).fetchall()
        self.assertEqual(len(evsBefore), len(evsAfterDelete), f'evidence was not deleted')


    def test_add_delete_evidence_negative(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        evsBefore = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 2",
            (self.tag_id_has_not,)
        ).fetchall()

        evidence = {
            "description": "this is a test evidence",
            "tag_id": self.tag_id_has_not,
            "type": 2,
            "item_id": self.item_id,
            "code_id": self.code_id,
            "created_by": self.user_id,
            "created": dbw.get_millis(),
        }
        evid = dbw.add_evidence_return_id(cur, evidence)
        evsAfter = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 2",
            (self.tag_id_has_not,)
        ).fetchall()
        self.assertEqual(len(evsBefore)+1, len(evsAfter), f'evidence was not added')

        dbw.delete_evidence(cur, [evid], EVIDENCE_PATH)
        evsAfterDelete = cur.execute(
            f"SELECT * FROM {TBL_EVIDENCE} WHERE tag_id = ? AND type = 2",
            (self.tag_id_has_not,)
        ).fetchall()
        self.assertEqual(len(evsBefore), len(evsAfterDelete), f'evidence was not deleted')


if __name__ == '__main__':
    unittest.main()
