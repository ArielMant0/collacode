"""
This module contains a Caribou migration.

Migration Name: initial
Migration Version: 20250711140131
"""

import os
from pathlib import Path

input_path = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("20250711140131_initial.sql")

def upgrade(connection):
    # add your upgrade step here
    with open(input_path, "r") as file:
        all_sql = file.read().split(";")[1:-2]

    for cmd in all_sql:
        connection.execute(cmd.replace("\n", ""))

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    tables = ["item_sim_counts", "item_sims"]

    for t in tables:
        connection.execute("drop table ?;", (t,))

    connection.commit()
