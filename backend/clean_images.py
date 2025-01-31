import sqlite3
from pathlib import Path

ALLOWED_EXTENSIONS = set(['.png', '.jpg', '.jpeg', '.gif', ".svg", ".mp4"])

def clean_teaser(dirpath, dbpath):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()

    sumAll = 0

    dirp = Path(dirpath)

    for file in dirp.glob("**/*"):
        if file.is_file() and file.suffix in ALLOWED_EXTENSIONS:
            t = cur.execute("SELECT id FROM items WHERE teaser = ?;", (file.name,)).fetchall()
            if t is None or len(t) == 0:
                sumAll += 1
                file.unlink(missing_ok=True)

    print(f"removed {sumAll} teaser files from {dirp}")

def clean_evidence(dirpath, dbpath):
    con = sqlite3.connect(dbpath)
    cur = con.cursor()

    sumAll = 0

    dirp = Path(dirpath)

    for file in dirp.glob("**/*"):
        if file.is_file() and file.suffix in ALLOWED_EXTENSIONS:
            e = cur.execute("SELECT id FROM evidence WHERE filepath = ?;", (file.name,)).fetchall()
            if e is None or len(e) == 0:
                sumAll += 1
                file.unlink(missing_ok=True)

    print(f"removed {sumAll} evidence files from {dirp}")

def clean(teaser, evidence, dbpath="./data/data.db"):
    clean_teaser(teaser, dbpath)
    clean_evidence(evidence, dbpath)

if __name__ == "__main__":
    clean("../public/teaser", "../public/evidence")
    clean("../dist/teaser", "../dist/evidence")