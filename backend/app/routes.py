import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import db_wrapper

from flask import request, Response, jsonify
from werkzeug.utils import secure_filename

from app import bp
from app.extensions import db

EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "dist", "evidence")
EVIDENCE_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "evidence")
TEASER_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "dist", "teaser")
TEASER_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "teaser")

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

@bp.get('/api/v1/datatags/dataset/<dataset>')
def get_datatags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    data = db_wrapper.get_datatags_by_dataset(cur, dataset)
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

@bp.get('/api/v1/evidence/dataset/<dataset>')
def get_evidence_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in evidence])

@bp.get('/api/v1/evidence/code/<code>')
def get_evidence_code(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    return jsonify([dict(d) for d in evidence])

@bp.get('/api/v1/tag_assignments/dataset/<dataset>')
def get_tag_assignments_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_tag_assignments_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in result])

@bp.get('/api/v1/tag_assignments/code/<code>')
def get_tag_assignments(code):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_tag_assignments_by_old_code(cur, code)
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

@bp.get('/api/v1/memos/dataset/<dataset>')
def get_memos_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    result = db_wrapper.get_memos_by_dataset(cur, dataset)
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
    if "memos" in request.json:
        db_wrapper.add_memos(cur, request.json["memos"])
    if "tag_assignments" in request.json:
        db_wrapper.add_tag_assignments(cur, request.json["tag_assignments"])
    if "code_transitions" in request.json:
        db_wrapper.add_code_transitions(cur, request.json["code_transitions"])

    db.commit()

    return Response(status=200)

@bp.post('/api/v1/add/games')
def add_games():
    cur = db.cursor()

    rows = request.json["rows"]
    for e in rows:

        name = e.get("teaserName", "")
        e["teaser"] = None

        if name:
            suff = [p.suffix for p in TEASER_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["teaser"] = name+suff

    db_wrapper.add_games(cur, request.json["dataset"], rows)
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

@bp.post('/api/v1/add/datatags')
def add_datatags():
    cur = db.cursor()
    db_wrapper.add_datatags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tags/assign')
def add_tags_for_assignment():
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    db_wrapper.add_tags_for_assignment(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tag_assignments')
def add_tag_assignments():
    cur = db.cursor()
    db_wrapper.add_tag_assignments(cur, request.json["rows"])
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
    rows = request.json["rows"]
    for e in rows:
        name = e.get("teaserName", "")
        filepath = e.get("teaser", "")

        if name:
            suff = [p.suffix for p in TEASER_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            if filepath:
                p = TEASER_PATH.joinpath(filepath)
                if p.exists():
                    p.unlink()
                p = TEASER_BACKUP.joinpath(filepath)
                if p.exists():
                    p.unlink()

            e["teaser"] = name+suff

    db_wrapper.update_games(cur, rows)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/evidence')
def update_evidence():
    cur = db.cursor()
    rows = request.json["rows"]
    for e in rows:
        name = e.get("filename", "")
        filepath = e.get("filepath", "")

        if name:
            suff = [p.suffix for p in EVIDENCE_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            if filepath:
                p = EVIDENCE_PATH.joinpath(filepath)
                if p.exists():
                    p.unlink()
                p = EVIDENCE_BACKUP.joinpath(filepath)
                if p.exists():
                    p.unlink()

            e["filepath"] = name+suff

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
    db_wrapper.delete_games(cur, request.json["ids"], TEASER_PATH, TEASER_BACKUP)
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

@bp.post('/api/v1/delete/evidence')
def delete_evidence():
    cur = db.cursor()
    db_wrapper.delete_evidence(cur, request.json["ids"], EVIDENCE_PATH, EVIDENCE_BACKUP)
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

@bp.post('/api/v1/image/evidence/<name>')
def upload_image_evidence(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(EVIDENCE_PATH.joinpath(filename))
        file.save(EVIDENCE_BACKUP.joinpath(filename))

    return Response(status=200)

@bp.post('/api/v1/image/teaser/<name>')
def upload_image_teaser(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(TEASER_PATH.joinpath(filename))
        file.save(TEASER_BACKUP.joinpath(filename))

    return Response(status=200)

@bp.post('/api/v1/split/tags')
def split_tags():
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    db_wrapper.split_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/merge/tags')
def merge_tags():
    cur = db.cursor()
    cur.row_factory = sqlite3.Row
    db_wrapper.merge_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/evidence')
def add_evidence():
    cur = db.cursor()

    rows = request.json["rows"]
    for e in rows:

        name = e["filename"]
        e["filepath"] = None

        if name:
            suff = [p.suffix for p in EVIDENCE_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name+suff

    db_wrapper.add_evidence(cur, rows)
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

    trans = db_wrapper.get_code_transitions_by_codes(cur, oldcode, newcode)

    if len(trans) > 0 and trans[0]["finished"] is not None:
        print("code transition already finished")
        return Response(status=500)

    now = datetime.now(timezone.utc).timestamp()
    db_wrapper.add_code_transitions(cur, [{ "old_code": oldcode, "new_code": newcode, "started": now }])
    db_wrapper.prepare_transition(cur, oldcode, newcode)
    db.commit()

    return Response(status=200)

@bp.post('/api/v1/finalize/codes/transition/old/<oldcode>/new/<newcode>')
def finalize_code_transition(oldcode, newcode):
    cur = db.cursor()

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    has_new = cur.execute("SELECT * FROM codes WHERE id = ?;", (newcode,)).fetchone()

    if not has_old or not has_new:
        print("codes missing for code transition")
        return Response(status=500)

    trans = db_wrapper.get_code_transitions_by_codes(cur, oldcode, newcode)

    if len(trans) > 0:
        print("transition does not exist")
        return Response(status=500)

    if trans[0]["finished"] is not None:
        print("transition already finished")
        return Response(status=500)

    db_wrapper.update_code_transitions(cur, [{ "old_code": oldcode, "new_code": newcode, "created_by": user_id, "created": created }])
    db.commit()

    return Response(status=200)