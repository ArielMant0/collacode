"""
This module contains a Caribou migration.

Migration Name: inital
Migration Version: 20241101165647
"""

import os
from pathlib import Path

input_path = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("20241101165647_inital.sql")


def upgrade(connection):
    # add your upgrade step here
    with open(input_path, "r") as file:
        all_sql = file.read().split(";")[1:-2]

    for cmd in all_sql:
        connection.execute(cmd.replace("\n", ""))

    connection.commit()


def downgrade(connection):
    # add your downgrade step here
    tables = [
        # Group
        "code_transitions",
        "codes",
        "users",
        # Group
        "datasets",
        "datatags",
        "evidence",
        # Group
        "ext_agreements",
        "ext_cat_connections",
        # Group
        "ext_categories",
        "ext_tag_connections",
        # Group
        "externalizations",
        "game_expertise",
        # Group
        "games",
        "logs",
        "memos",
        "memo_links",
        # Group
        "tag_assignments",
        "tags",
        "update_times",
    ]

    # does not work for some reason
    for t in tables:
        connection.execute("drop table ?;", (t,))

    connection.commit()
