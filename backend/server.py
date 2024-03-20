import os
import sqlite3
import numpy as np
from pathlib import Path
import db_wrapper

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

@app.get('/api/v1/datasets')
def datasets():
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    datasets = db_wrapper.get_datasets(cur)
    return jsonify([dict(d) for d in datasets])

@app.get('/api/v1/games/dataset/<dataset>')
def get_games_data(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_games_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/users/dataset/<dataset>')
def get_users_data(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_users_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/codes/dataset/<dataset>')
def get_codes_dataset(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_codes_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/tags/dataset/<dataset>')
def get_tags_dataset(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_tags_by_dataset(cur, dataset)
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
    data = db_wrapper.get_datatags_by_code(cur, code)
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/datatags/tag/<tag>')
def get_datatags_tag(tag):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_datatags_by_tag(cur, tag)
    return jsonify([dict(d) for d in data])

@app.get('/api/v1/image_evidence/dataset/<dataset>')
def get_image_evidence_dataset(dataset):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in evidence])

@app.get('/api/v1/image_evidence/code/<code>')
def get_image_evidence_code(code):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    return jsonify([dict(d) for d in evidence])

@app.get('/api/v1/tag_groups/old/<oldcode>/new/<newcode>')
def get_tag_groups(oldcode, newcode):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_tag_groups_by_codes(cur, oldcode, newcode)
    return jsonify([dict(d) for d in result])

@app.get('/api/v1/code_transitions/code/<code>')
def get_code_transitions(code):
    cur = con.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_code_transitions_by_old_code(cur, code)
    return jsonify([dict(d) for d in result])

@app.post('/api/v1/add/dataset')
def add_dataset():
    cur = con.cursor()
    name = request.json["name"]
    desc = request.json["description"] if "description" in request.json else ""
    db_wrapper.add_dataset(cur, name, desc)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/add/all')
def add_all():
    cur = con.cursor()

    if "dataset" not in request.json:
        return Response(status=500)

    dataset = request.json["dataset"]
    ds_id = cur.execute("SELECT id FROM datasets WHERE name = ?;", (dataset,)).fetchone()[0]
    games = request.json["games"] if "games" in request.json else []
    db_wrapper.add_games(cur, ds_id, games)

    users = request.json["users"] if "users" in request.json else []
    db_wrapper.add_users(cur, ds_id, users)

    codes = request.json["codes"] if "codes" in request.json else []
    db_wrapper.add_codes(cur, ds_id, codes)

    tags = request.json["tags"] if "tags" in request.json else []
    db_wrapper.add_tags(cur, tags)

    datatags = request.json["datatags"] if "datatags" in request.json else []
    db_wrapper.add_datatags(cur, datatags)

    evidence = request.json["evidence"] if "evidence" in request.json else []
    db_wrapper.add_datatags(cur, evidence)

    con.commit()

    return Response(status=200)

@app.post('/api/v1/add/games')
def add_games():
    cur = con.cursor()
    db_wrapper.add_games(cur, request.json["dataset"], request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/add/codes')
def add_codes():
    cur = con.cursor()
    db_wrapper.add_codes(cur, request.json["dataset"], request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/add/tag_groups')
def add_tag_groups():
    cur = con.cursor()
    print(request.json["rows"])
    db_wrapper.add_tag_groups(cur, request.json["dataset"], request.json["old_code"], request.json["new_code"], request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/add/code_transitions')
def add_code_transitions():
    cur = con.cursor()
    db_wrapper.add_code_transitions(cur, request.json["group"], request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/update/codes')
def update_codes():
    cur = con.cursor()
    db_wrapper.update_codes(cur, request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/update/games')
def update_games():
    cur = con.cursor()
    db_wrapper.update_games(cur, request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/update/image_evidence')
def update_image_evidence():
    cur = con.cursor()
    db_wrapper.update_evidence(cur, request.json["rows"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/games')
def delete_games():
    cur = con.cursor()
    db_wrapper.delete_games(cur, request.json["ids"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/datatags')
def delete_game_datatags():
    cur = con.cursor()
    db_wrapper.delete_datatags(cur, request.json["ids"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/image_evidence')
def delete_image_evidence():
    cur = con.cursor()
    db_wrapper.delete_evidence(cur, request.json["ids"], IMAGE_PATH)
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/tag_groups')
def delete_tag_groups():
    cur = con.cursor()
    db_wrapper.delete_tag_groups(cur, request.json["ids"])
    con.commit()
    return Response(status=200)

@app.post('/api/v1/delete/code_transitions')
def delete_code_transitions():
    cur = con.cursor()
    db_wrapper.delete_code_transitions(cur, request.json["ids"])
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
    code_id = request.json["code_id"]
    user_id = request.json["user_id"]
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

    db_wrapper.add_evidence(cur, [{
        "game_id": game_id,
        "code_id": code_id,
        "filepath": name+suff,
        "description": request.json["description"],
        "created": request.json["created"],
        "created_by": user_id,
    }])
    con.commit()

    return Response(status=200)


@app.post('/api/v1/update/game/datatags')
def update_game_datatags():
    cur = con.cursor()
    db_wrapper.update_game_datatags(cur, request.json)
    con.commit()
    return Response(status=200)

app.run(port=8000)