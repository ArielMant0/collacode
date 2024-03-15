import os
import sqlite3
import numpy as np
from pathlib import Path

from flask import request, Flask, Response, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

DB_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("data", "data.db")
IMAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "public", "image_evidence")
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif', "svg" }

con = sqlite3.connect(DB_PATH, check_same_thread=False)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_file_suffix(filename):
    idx = filename.rfind(".")
    if idx > 0:
        return filename[idx+1:]
    return "png"

def make_space(length):
    return ",".join(["?"] * length)

@app.get('/api/v1/datasets')
def datasets():
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    datasets = cur.execute("SELECT * from datasets").fetchall()
    return jsonify([dict(d) for d in datasets])

@app.get('/api/v1/games/dataset/<dataset>')
def get_games_data(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = cur.execute("SELECT * from games WHERE dataset_id = ?;", (dataset,)).fetchall()
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/users/dataset/<dataset>')
def get_users_data(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = cur.execute("SELECT * from users WHERE dataset_id = ?;", (dataset,)).fetchall()
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/codes/dataset/<dataset>')
def get_codes_dataset(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = cur.execute("SELECT * from codes WHERE dataset_id = ?;", (dataset,)).fetchall()
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/tags/dataset/<dataset>')
def get_tags_dataset(dataset):
    cur = con.cursor()
    codes = cur.execute("SELECT id from codes WHERE dataset_id = ?;", (dataset,)).fetchall()
    codes = [t[0] for t in codes]
    cur.row_factory = sqlite3.Row
    data = cur.execute(f"SELECT * from tags WHERE code_id IN ({make_space(len(codes))});", codes).fetchall()
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/tags/code/<code>')
def get_tags_code(code):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = cur.execute("SELECT * from tags WHERE code_id = ?;", (code,)).fetchall()
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/datatags/code/<code>')
def get_datatags_code(code):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = cur.execute("SELECT * from datatags WHERE code_id = ?;", (code,)).fetchall()
    print([dict(d) for d in data])
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/datatags/tag/<tag>')
def get_datatags_tag(tag):
    cur = con.cursor()
    data = cur.execute("SELECT * from datatags WHERE tag_id = ?;", (tag,)).fetchall()
    return jsonify([dict(d) for d in data])

@app.route('/api/v1/image_evidence/dataset/<dataset>', methods=['GET'])
def image_evidence(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    evidence = cur.execute(
        """SELECT * from image_evidence LEFT JOIN games ON image_evidence.game_id = games.id WHERE games.dataset_id = ?;""",
        (dataset, )
    ).fetchall()
    return jsonify([dict(d) for d in evidence])

@app.post('/api/v1/add/games')
def add():
    cur = con.cursor()
    data = []
    stmt = "INSERT OR IGNORE INTO games (dataset_id, name, year, played, url) VALUES (?, ?, ?, ?, ?);"
    dataset = request.json["dataset"]
    for d in request.json["rows"]:
        data.append((dataset, d["name"], d["year"], d["played"], d["url"]))

    cur.executemany(stmt, data)
    con.commit()

    return Response(status=200)

@app.post('/api/v1/update/games')
def update_games():
    cur = con.cursor()

    data = []
    rows = request.json["rows"]
    for game in rows:
        played = 1 if game["played"] == 1 or game["played"] == True or game["played"] == "yes" else 0
        data.append((game["name"], game["year"], played, game["url"], game["id"]))

    cur.executemany("UPDATE games SET name = ?, year = ?, played = ?, url = ? WHERE id = ?;", data)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/update/image_evidence')
def update_image_evidence():
    cur = con.cursor()

    data = []
    rows = request.json["rows"]
    for r in rows:
        data.append((r["description"], r["id"]))

    cur.executemany("UPDATE image_evidence SET description = ? WHERE id = ?;", data)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/games')
def delete_games():
    cur = con.cursor()
    ids = [(id,) for id in request.json["ids"]]
    cur.executemany("DELETE FROM games WHERE id = ?;", ids)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/datatags')
def delete_game_datatags():
    cur = con.cursor()
    ids = [(id,) for id in request.json["ids"]]
    ids = request.json["ids"]
    cur.executemany("DELETE FROM datatags WHERE id = ?;", ids)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/image_evidence')
def delete_image_evidence():
    cur = con.cursor()
    ids = request.json["ids"]
    filenames = cur.execute(f"SELECT filepath FROM image_evidence WHERE id IN ({make_space(len(ids))});", ids).fetchall()
    cur.executemany("DELETE FROM image_evidence WHERE id = ?;", [(id,) for id in ids])

    for f in filenames:
        IMAGE_PATH.joinpath(f[0]).unlink(missing_ok=True)

    con.commit()
    return Response(status=200)

@app.post('/api/v1/image/image_evidence/<name>')
def upload_image(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(IMAGE_PATH.joinpath(filename))

    return Response(status=200)

@app.post('/api/v1/add/game/image_evidence')
def add_image_evidence():
    cur = con.cursor()
    game_id = request.json["game_id"]
    user_id = request.json["user_id"]
    created = request.json["created"]
    desc = request.json["description"]
    name = request.json["name"]

    suff = [p.suffix for p in IMAGE_PATH.glob(name+".*")][0]
    if not suff:
        print("image does not exist")
        return Response(status=500)

    game = cur.execute("SELECT * FROM games WHERE id = ?;", (game_id,)).fetchone()
    user = cur.execute("SELECT * FROM users WHERE id = ?;", (user_id,)).fetchone()
    if not game or not user:
        print("game or user does not exist")
        return Response(status=500)

    cur.execute(
        "INSERT INTO image_evidence (game_id, description, filepath, created, created_by) VALUES (?, ?, ?, ?, ?);",
        (game_id, desc, name+suff, created, user_id)
    )
    con.commit()

    return Response(status=200)


@app.post('/api/v1/update/game/datatags')
def update_game_datatags():
    cur = con.cursor()
    code_id = request.json["code_id"]
    user_id = request.json["user_id"]
    game_id = request.json["game_id"]
    created = request.json["created"]

    # remove datatags not in the list
    tokeep = [int(d["tag_id"]) for d in request.json["tags"] if "tag_id" in d]
    results = cur.execute("SELECT id FROM datatags WHERE game_id = ? AND code_id = ? AND created_by = ?;", (game_id, code_id, user_id))
    existing = [d[0] for d in results.fetchall()]
    toremove = np.setdiff1d(np.array(existing), np.array(tokeep)).tolist()

    if len(toremove) > 0:
        print(f"deleting {len(toremove)} data tags")
        print(toremove)
        stmt = f"DELETE FROM datatags WHERE created_by = ? AND id IN ({make_space(len(toremove))});"
        cur.execute(stmt, [user_id] + toremove)
        con.commit()

    # add datatags where tags already exist in the database
    toadd = np.setdiff1d(np.array(tokeep), np.array(existing)).tolist()

    if len(toadd) > 0:
        stmt = "INSERT INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
        data = []
        for d in toadd:
            data.append((game_id, int(d), code_id, created, user_id))

        print(toadd)
        print(f"adding {len(data)} data tags for existing tags")
        print(toadd)
        cur.executemany(stmt, data)
        con.commit()

    # add tags that do not exist in the database
    newtags = [d["tag_name"] for d in request.json["tags"] if "tag_name" in d]
    newtags_desc = [d["description"] for d in request.json["tags"] if "tag_name" in d]

    if len(newtags) > 0:
        stmt = "INSERT INTO tags (name, description, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
        data = []
        for i, d in enumerate(newtags):
            data.append((d, newtags_desc[i], code_id, created, user_id))
        # collect new tag ids
        print(f"adding {len(data)} new tags")
        print(newtags)
        cur.executemany(stmt, data)
        con.commit()

        result = cur.execute(f"SELECT id FROM tags WHERE created_by = ? AND name IN ({make_space(len(newtags))});", [user_id] + newtags)
        new_tag_ids = [d[0] for d in result]

        # add datatags for new these tags
        if len(new_tag_ids) > 0:
            data = []
            stmt = "INSERT INTO datatags (game_id, tag_id, code_id, created, created_by) VALUES (?, ?, ?, ?, ?);"
            for d in new_tag_ids:
                data.append((game_id, d, code_id, created, user_id))

            print(f"adding {len(data)} data tags for new tags")
            print(new_tag_ids)
            cur.executemany(stmt, data)
            con.commit()

    return Response(status=200)

app.run(port=8000)