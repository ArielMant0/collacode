import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import db_wrapper

from flask import request, Response, jsonify
from werkzeug.utils import secure_filename

from app import bp
from app.extensions import db

IMAGE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "image_evidence")
ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif', "svg" }

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
def get_file_suffix(filename):
    idx = filename.rfind(".")
    if idx > 0:
        return filename[idx+1:]
    return "png"

@bp.get('/api/v1/datasets')
def datasets():
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    datasets = db_wrapper.get_datasets(cur)
    return jsonify([dict(d) for d in datasets])

@bp.get('/api/v1/games/dataset/<dataset>')
def get_games_data(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_games_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/users/dataset/<dataset>')
def get_users_data(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_users_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/codes/dataset/<dataset>')
def get_codes_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_codes_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/tags/dataset/<dataset>')
def get_tags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_tags_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/tags/code/<code>')
def get_tags_code(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_tags_by_code(cur, code)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/datatags/code/<code>')
def get_datatags_code(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_datatags_by_code(cur, code)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/datatags/tag/<tag>')
def get_datatags_tag(tag):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_datatags_by_tag(cur, tag)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/image_evidence/dataset/<dataset>')
def get_image_evidence_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in evidence])

@bp.get('/api/v1/image_evidence/code/<code>')
def get_image_evidence_code(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    return jsonify([dict(d) for d in evidence])

@bp.get('/api/v1/tag_assignments/code/<code>')
def get_tag_assignments(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_tag_assignments_by_old_code(code)
    return jsonify([dict(d) for d in result])

@bp.get('/api/v1/tag_assignments/old/<old_code>/new/<new_code>')
def get_tag_assignments_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_tag_assignments_by_codes(cur, old_code, new_code)
    return jsonify([dict(d) for d in result])

@bp.get('/api/v1/code_transitions/dataset/<dataset>')
def get_code_transitions(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_code_transitions_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in result])

@bp.get('/api/v1/code_transitions/code/<code>')
def get_code_transitions_by_code(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_code_transitions_by_old_code(cur, code)
    return jsonify([dict(d) for d in result])

@bp.get('/api/v1/code_transitions/old/<old_code>/new/<new_code>')
def get_code_transitions_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_code_transitions_by_codes(cur, old_code, new_code)
    return jsonify([dict(d) for d in result])

@bp.post('/api/v1/add/dataset')
def add_dataset():
    cur = db.cursor()
    name = request.json["name"]
    desc = request.json["description"] if "description" in request.json else ""
    db_wrapper.add_dataset(cur, name, desc)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/upload')
def upload_data():
    cur = db.cursor()

    if "dataset" not in request.json:
        return Response(status=500)

    dataset = request.json["dataset"]
    ds_id = cur.execute("SELECT id FROM datasets WHERE name = ?;", (dataset,)).fetchone()[0]

    if "games" in request.json:
        db_wrapper.add_games(cur, ds_id, request.json["games"])
    if "users" in request.json:
        db_wrapper.add_users(cur, ds_id, request.json["users"])
    if "codes" in request.json:
        db_wrapper.add_codes(cur, ds_id, request.json["codes"])
    if "tags" in request.json:
        db_wrapper.add_tags(cur, request.json["tags"])
    if "datatags" in request.json:
        db_wrapper.add_datatags(cur, request.json["datatags"] )
    if "evidence" in request.json:
        db_wrapper.add_evidence(cur, request.json["evidence"])
    if "tag_assignments" in request.json:
        db_wrapper.add_tag_assignments(cur, request.json["tag_assignments"])
    if "code_transitions" in request.json:
        db_wrapper.add_code_transitions(cur, request.json["code_transitions"])

    db.commit()

    return Response(status=200)

@bp.post('/api/v1/add/games')
def add_games():
    cur = db.cursor()
    db_wrapper.add_games(cur, request.json["dataset"], request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/codes')
def add_codes():
    cur = db.cursor()
    db_wrapper.add_codes(cur, request.json["dataset"], request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tags')
def add_tags():
    cur = db.cursor()
    db_wrapper.add_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tag_assignments')
def add_tag_assignments():
    cur = db.cursor()
    db_wrapper.add_tag_assignments(cur, request.json["old_code"], request.json["new_code"], request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/code_transitions')
def add_code_transitions():
    cur = db.cursor()
    db_wrapper.add_code_transitions(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/codes')
def update_codes():
    cur = db.cursor()
    db_wrapper.update_codes(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/tags')
def update_tags():
    cur = db.cursor()
    db_wrapper.update_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/games')
def update_games():
    cur = db.cursor()
    db_wrapper.update_games(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/image_evidence')
def update_image_evidence():
    cur = db.cursor()
    db_wrapper.update_evidence(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/tag_assignments')
def update_tag_assignments():
    cur = db.cursor()
    db_wrapper.update_tag_assignments(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/games')
def delete_games():
    cur = db.cursor()
    db_wrapper.delete_games(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/tags')
def delete_tags():
    cur = db.cursor()
    db_wrapper.delete_tags(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/datatags')
def delete_game_datatags():
    cur = db.cursor()
    db_wrapper.delete_datatags(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/image_evidence')
def delete_image_evidence():
    cur = db.cursor()
    db_wrapper.delete_evidence(cur, request.json["ids"], IMAGE_PATH)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/tag_assignments')
def delete_tag_assignments():
    cur = db.cursor()
    db_wrapper.delete_tag_assignments(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/code_transitions')
def delete_code_transitions():
    cur = db.cursor()
    db_wrapper.delete_code_transitions(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/image/image_evidence/<name>')
def upload_image(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(IMAGE_PATH.joinpath(filename))

    return Response(status=200)

@bp.post('/api/v1/add/game/image_evidence')
def add_image_evidence():
    cur = db.cursor()
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
    db.commit()

    return Response(status=200)


@bp.post('/api/v1/update/game/datatags')
def update_game_datatags():
    cur = db.cursor()
    db_wrapper.update_game_datatags(cur, request.json)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/start/codes/transition/old/<oldcode>/new/<newcode>')
def start_code_transition(oldcode, newcode):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    has_new = cur.execute("SELECT * FROM codes WHERE id = ?;", (newcode,)).fetchone()

    if not has_old or not has_new:
        print("codes missing for code transition")
        return Response(status=500)

    tags = db_wrapper.get_tags_by_code(cur, newcode)
    assigs = db_wrapper.get_tag_assignments_by_codes(cur, oldcode, newcode)

    if len(tags) > 0 and len(assigs) > 0:
        return Response(status=200)

    db_wrapper.copy_tags_for_transition(cur, oldcode, newcode)
    return Response(status=200)


@bp.post('/api/v1/finalize/codes/transition/old/<oldcode>/new/<newcode>/user/<user>')
def finalize_code_transition(oldcode, newcode, user):
    cur = db.cursor()

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    has_new = cur.execute("SELECT * FROM codes WHERE id = ?;", (newcode,)).fetchone()
    has_user = cur.execute("SELECT * FROM users WHERE id = ?;", (user,)).fetchone()

    # TODO

    # if not has_old or not has_new:
    #     print("codes missing for code transition")
    #     return Response(status=500)

    # if not has_user:
    #     print("user does not exist")
    #     return Response(status=500)

    # created = datetime.now(timezone.utc).timestamp()

    # cur.row_factory = sqlite3.Row
    # tag_groups = db_wrapper.get_tag_groups_by_codes(cur, oldcode, newcode)

    # # for each tag group: create a new tag in the new code
    # for tg in tag_groups:

    #     # add the new tag
    #     cur = cur.execute(
    #         "INSERT OR IGNORE INTO tags (code_id, name, description, created, created_by) VALUES (?, ?, ?, ?, ?) RETURNING id;",
    #         (newcode, tg["name"], tg["description"], created, user)
    #     )
    #     tid = next(cur)
    #     code_trans = db_wrapper.get_code_transitions_by_tag_group(cur, tg.id)

    #     # for each original tag: create a datatag in the new code (with the new tag)
    #     for ct in code_trans:
    #         rows = []
    #         # get all games for the original tag
    #         games = db_wrapper.get_datatags_by_tag(cur, ct.tag_id)
    #         for g in games:
    #             rows.append((g.id, tid, newcode, created, user))

    #         # add the new datatags
    #         db_wrapper.add_datatags(cur, rows)

    db.commit()

    return Response(status=200)