import os
import sqlite3
import unittest

from pathlib import Path

import config
import app.db_wrapper as dbw

from table_constants import (
    TBL_DATATAGS,
    TBL_ITEMS,
    TBL_ITEMS_FINAL
)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "data", "data-test.db"
).resolve()

class ItemsFinalizedTestCase(unittest.TestCase):

    def setUp(self):
        self.db = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.dataset_id = 1
        self.code_id = 1
        self.user_id = 1

        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        # get an item that is not finalized
        item = cur.execute(
            f"""SELECT DISTINCT i.id FROM {TBL_ITEMS} i
            WHERE NOT EXISTS (
                SELECT 1
                FROM {TBL_ITEMS_FINAL} f
                WHERE f.item_id = i.id AND f.user_id = ?
            ) AND i.dataset_id = ? LIMIT 1;""",
            (self.user_id, self.dataset_id)
        ).fetchone()
        self.item_id = item.id


    def tearDown(self):
        self.db.rollback()


    def test_finalize(self):
        self.db.row_factory = dbw.namedtuple_factory
        cur = self.db.cursor()

        dbw.finalize_items(cur, [{ "item_id": self.item_id, "user_id": self.user_id }])
        finalized = dbw.get_items_finalized_by_user(cur, self.user_id)
        isFinal = len(
            [f for f in finalized if f.item_id == self.item_id and f.user_id == self.user_id]
        ) > 0

        self.assertTrue(isFinal, f'item was not finalized')


if __name__ == '__main__':
    unittest.main()
