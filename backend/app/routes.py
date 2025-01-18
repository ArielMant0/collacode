import os
from uuid import uuid4
import requests
import db_wrapper
import app.user_manager as user_manager

from base64 import b64decode
from datetime import datetime, timezone
from pathlib import Path
from shutil import copyfile
import flask_login

from flask import request, Response, jsonify
from werkzeug.utils import secure_filename

from app import bp
import app.user_manager as user_mgr
from app.extensions import db, login_manager
from app.steam_api_loader import get_gamedata_from_id, get_gamedata_from_name

EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "dist", "evidence")
EVIDENCE_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "evidence")
TEASER_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "dist", "teaser")
TEASER_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath("..", "..", "public", "teaser")

ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'gif', "svg", "mp4" }

IGNORE_TAGS = ["camera movement rotation", "camera type", "cutscenes cinematics", "iso perspective"]

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_suffix(filename):
    idx = filename.rfind(".")
    if idx > 0:
        return filename[idx+1:]
    return "png"

def get_ignore_tags(cur):
    result = cur.execute(f"SELECT id FROM tags WHERE name IN ({db_wrapper.make_space(len(IGNORE_TAGS))});", IGNORE_TAGS).fetchall()
    resultAll = cur.execute(f"SELECT id, parent FROM tags WHERE parent IS NOT NULL").fetchall()
    ids = [t["id"] for t in result]
    changes = True
    while changes:
        children = [d["id"] for d in resultAll if d["parent"] is not None and d["parent"] in ids and d["id"] not in ids]
        changes = len(children) > 0
        for child in children:
            ids.append(child)
    return ids

def filter_ignore(cur, data, attr="id", excluded=None):
    excluded = get_ignore_tags(cur) if excluded is None else excluded
    return [d for d in data if d[attr] not in excluded]


@login_manager.user_loader
def user_loader(user_id):
    return user_mgr.get_user(user_id)

@bp.get('/api/v1/user_login')
def get_user_login():
    if flask_login.current_user and flask_login.current_user.is_authenticated:
        flask_login.confirm_login()
        return jsonify({ "id": flask_login.current_user.id })

    return Response(status=403)

@bp.route('/api/v1/login', methods=['GET', 'POST'])
def login():
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        Response(status=400)

    auth_value = auth_header.split(" ")
    name, pw = b64decode(auth_value[1]).decode().split(":")
    user = user_manager.get_user_by_name(name)

    if user:
        # login and validate the user
        user.authenticate(pw)
        if flask_login.login_user(user, remember=True):
            return jsonify({ "id": user.id })
        else:
            return Response(status=403)

    return Response(status=404)

@bp.route('/api/v1/logout', methods=['GET', 'POST'])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return Response(status=200)

@bp.post('/api/v1/user_pwd')
@flask_login.login_required
def change_password():
    user = flask_login.current_user
    if user.is_authenticated:
        oldpw = b64decode(request.args.get("old", "")).decode()
        newpw = b64decode(request.args.get("new", "")).decode()
        if user.try_change_pwd(oldpw, newpw):
            return Response(status=200)

        return Response(status=500)

    return Response(status=403)

@bp.get('/api/v1/lastupdate')
def get_last_update():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    return jsonify([dict(d) for d in db_wrapper.get_last_updates(cur) ])

@bp.get('/api/v1/import_game/steam/id/<steamid>')
def import_from_steam_id(steamid):
    result = get_gamedata_from_id(str(steamid))
    return jsonify(result)

@bp.get('/api/v1/import_game/steam/name/<steamname>')
def import_from_steam_name(steamname):
    result = get_gamedata_from_name(steamname)
    if len(result) == 0:
        return jsonify({ "multiple": True, "data": [] })
    return jsonify({
        "multiple": len(result) > 1,
        "data": result if len(result) > 1 else result[0]
    })

@bp.get('/api/v1/datasets')
def datasets():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    datasets = db_wrapper.get_datasets(cur)
    return jsonify([dict(d) for d in datasets])

@bp.get('/api/v1/items/dataset/<dataset>')
def get_items_data(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_items_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/item_expertise/dataset/<dataset>')
def get_item_expertise(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_item_expertise_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/users/dataset/<dataset>')
def get_users_data(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_users_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/codes/dataset/<dataset>')
def get_codes_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_codes_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])

@bp.get('/api/v1/tags/dataset/<dataset>')
def get_tags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_dataset(cur, dataset)
    result = filter_ignore(cur, [dict(d) for d in data])
    return jsonify(result)

@bp.get('/api/v1/tags/code/<code>')
def get_tags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_code(cur, code)
    result = filter_ignore(cur, [dict(d) for d in data])
    return jsonify(result)

@bp.get('/api/v1/datatags/dataset/<dataset>')
def get_datatags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_dataset(cur, dataset)
    result = filter_ignore(cur, [dict(d) for d in data], attr="tag_id")
    return jsonify(result)

@bp.get('/api/v1/datatags/code/<code>')
def get_datatags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_code(cur, code)
    result = filter_ignore(cur, [dict(d) for d in data], attr="tag_id")
    return jsonify(result)

@bp.get('/api/v1/datatags/tag/<tag>')
def get_datatags_tag(tag):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_tag(cur, tag)
    result = filter_ignore(cur, [dict(d) for d in data], attr="tag_id")
    return jsonify(result)

@bp.get('/api/v1/evidence/dataset/<dataset>')
def get_evidence_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    result = filter_ignore(cur, [dict(d) for d in evidence], attr="tag_id")
    return jsonify(result)

@bp.get('/api/v1/evidence/code/<code>')
def get_evidence_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    result = filter_ignore(cur, [dict(d) for d in evidence], attr="tag_id")
    return jsonify(result)

@bp.get('/api/v1/tag_assignments/dataset/<dataset>')
def get_tag_assignments_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_dataset(cur, dataset)
    ex = get_ignore_tags(cur)
    result = filter_ignore(cur, [dict(d) for d in tas], attr="old_tag", excluded=ex)
    result = filter_ignore(cur, result, attr="new_tag", excluded=ex)
    return jsonify(result)

@bp.get('/api/v1/tag_assignments/code/<code>')
def get_tag_assignments(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_old_code(cur, code)
    ex = get_ignore_tags(cur)
    result = filter_ignore(cur, [dict(d) for d in tas], attr="old_tag", excluded=ex)
    result = filter_ignore(cur, result, attr="new_tag", excluded=ex)
    return jsonify(result)

@bp.get('/api/v1/tag_assignments/old/<old_code>/new/<new_code>')
def get_tag_assignments_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_codes(cur, old_code, new_code)
    ex = get_ignore_tags(cur)
    result = filter_ignore(cur, [dict(d) for d in tas], attr="old_tag", excluded=ex)
    result = filter_ignore(cur, result, attr="new_tag", excluded=ex)
    return jsonify(result)

@bp.get('/api/v1/code_transitions/dataset/<dataset>')
def get_code_transitions(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_dataset(cur, dataset)
    return jsonify(result)

@bp.get('/api/v1/code_transitions/code/<code>')
def get_code_transitions_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_old_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/code_transitions/old/<old_code>/new/<new_code>')
def get_code_transitions_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_codes(cur, old_code, new_code)
    return jsonify(result)

@bp.get('/api/v1/memos/dataset/<dataset>')
def get_memos_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_memos_by_dataset(cur, dataset)
    return jsonify(result)

@bp.get('/api/v1/meta_groups/code/<code>')
def get_meta_groups_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_groups_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_items/code/<code>')
def get_mitems_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_items_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_categories/code/<code>')
def get_meta_cats_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_categories_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_agreements/code/<code>')
def get_meta_agree_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_agreements_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_cat_connections/code/<code>')
def get_meta_cat_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_cat_conns_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_tag_connections/code/<code>')
def get_meta_tag_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_tag_conns_by_code(cur, code)
    return jsonify(result)

@bp.get('/api/v1/meta_ev_connections/code/<code>')
def get_meta_ev_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_ev_conns_by_code(cur, code)
    return jsonify(result)

@bp.post('/api/v1/add/dataset')
@flask_login.login_required
def add_dataset():
    cur = db.cursor()
    name = request.json["name"]
    desc = request.json["description"] if "description" in request.json else ""
    db_wrapper.add_dataset(cur, name, desc)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/upload')
@flask_login.login_required
def upload_data():
    cur = db.cursor()

    # TODO: rework required
    if "dataset" not in request.json:
        return Response(status=500)

    dataset = request.json["dataset"]
    ds_id = cur.execute("SELECT id FROM datasets WHERE name = ?;", (dataset,)).fetchone()[0]

    if "items" in request.json:
        db_wrapper.add_items(cur, ds_id, request.json["items"])
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

@bp.post('/api/v1/add/items')
@flask_login.login_required
def add_items():
    cur = db.cursor()

    rows = request.json["rows"]
    for e in rows:

        name = e.get("teaserName", "")
        url = e.get("teaserUrl", "")
        e["teaser"] = None

        if url:
            response = requests.get(url)
            if response.status_code == 200:
                suff = get_file_suffix(url.split("/")[-1])
                name = str(uuid4())
                filename = name + "." + suff
                filepath = TEASER_PATH.joinpath(filename)
                with open(filepath, "wb") as fp:
                    fp.write(response.content)
                copyfile(filepath, TEASER_BACKUP.joinpath(filename))
                print(f"saved downloaded image to {name}.{suff}")
                e["teaser"] = filename
        elif name:
            suff = [p.suffix for p in TEASER_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["teaser"] = name+suff

    db_wrapper.add_items(cur, request.json["dataset"], rows)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/item_expertise')
@flask_login.login_required
def add_item_expertise():
    cur = db.cursor()
    db_wrapper.add_item_expertise(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/codes')
@flask_login.login_required
def add_codes():
    cur = db.cursor()
    db_wrapper.add_codes(cur, request.json["dataset"], request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tags')
@flask_login.login_required
def add_tags():
    cur = db.cursor()
    db_wrapper.add_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/datatags')
@flask_login.login_required
def add_datatags():
    cur = db.cursor()
    db_wrapper.add_datatags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/tags/assign')
@flask_login.login_required
def add_tags_for_assignment():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
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
@flask_login.login_required
def add_code_transitions():
    cur = db.cursor()
    db_wrapper.add_code_transitions(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/meta_items')
@flask_login.login_required
def add_meta_items():
    cur = db.cursor()
    db_wrapper.add_meta_items(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/meta_agreements')
@flask_login.login_required
def add_meta_agreements():
    cur = db.cursor()
    db_wrapper.add_meta_agreements(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/meta_categories')
@flask_login.login_required
def add_meta_categories():
    cur = db.cursor()
    db_wrapper.add_meta_categories(cur,
        request.json["dataset"],
        request.json["code"],
        request.json["rows"]
    )
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/codes')
@flask_login.login_required
def update_codes():
    cur = db.cursor()
    db_wrapper.update_codes(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/tags')
@flask_login.login_required
def update_tags():
    cur = db.cursor()
    db_wrapper.update_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/item_expertise')
@flask_login.login_required
def update_item_expertise():
    cur = db.cursor()
    db_wrapper.update_item_expertise(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/items')
@flask_login.login_required
def update_items():
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

    db_wrapper.update_items(cur, rows)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/evidence')
@flask_login.login_required
def update_evidence():
    cur = db.cursor()
    rows = request.json["rows"]
    for e in rows:
        name = e.get("filename", "")

        if name:
            suff = [p.suffix for p in EVIDENCE_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name+suff

    db_wrapper.update_evidence(cur, request.json["rows"], EVIDENCE_PATH, EVIDENCE_BACKUP)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/tag_assignments')
@flask_login.login_required
def update_tag_assignments():
    cur = db.cursor()
    db_wrapper.update_tag_assignments(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/meta_groups')
@flask_login.login_required
def update_meta_groups():
    cur = db.cursor()
    db_wrapper.update_meta_groups(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/meta_items')
@flask_login.login_required
def update_meta_items():
    cur = db.cursor()
    db_wrapper.update_meta_items(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/meta_agreements')
@flask_login.login_required
def update_meta_agreements():
    cur = db.cursor()
    db_wrapper.update_meta_agreements(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/update/meta_categories')
@flask_login.login_required
def update_meta_categories():
    cur = db.cursor()
    db_wrapper.update_meta_categories(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/items')
@flask_login.login_required
def delete_items():
    cur = db.cursor()
    db_wrapper.delete_items(cur, request.json["ids"], TEASER_PATH, TEASER_BACKUP)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/tags')
@flask_login.login_required
def delete_tags():
    cur = db.cursor()
    db_wrapper.delete_tags(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/item_expertise')
@flask_login.login_required
def delete_item_expertise():
    cur = db.cursor()
    db_wrapper.delete_item_expertise(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/datatags')
@flask_login.login_required
def delete_datatags():
    cur = db.cursor()
    db_wrapper.delete_datatags(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/evidence')
@flask_login.login_required
def delete_evidence():
    cur = db.cursor()
    db_wrapper.delete_evidence(cur, request.json["ids"], EVIDENCE_PATH, EVIDENCE_BACKUP)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/tag_assignments')
@flask_login.login_required
def delete_tag_assignments():
    cur = db.cursor()
    db_wrapper.delete_tag_assignments(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/code_transitions')
@flask_login.login_required
def delete_code_transitions():
    cur = db.cursor()
    db_wrapper.delete_code_transitions(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/meta_items')
@flask_login.login_required
def delete_meta_items():
    cur = db.cursor()
    db_wrapper.delete_meta_items(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/meta_agreements')
@flask_login.login_required
def delete_meta_agreements():
    cur = db.cursor()
    db_wrapper.delete_meta_agreements(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/delete/meta_categories')
@flask_login.login_required
def delete_meta_categories():
    cur = db.cursor()
    db_wrapper.delete_meta_categories(cur, request.json["ids"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/image/evidence/<name>')
@flask_login.login_required
def upload_image_evidence(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(EVIDENCE_PATH.joinpath(filename))
        copyfile(EVIDENCE_PATH.joinpath(filename), EVIDENCE_BACKUP.joinpath(filename))

    return Response(status=200)

@bp.post('/api/v1/image/teaser/<name>')
@flask_login.login_required
def upload_image_teaser(name):
    if "file" not in request.files:
        return Response(status=500)

    file = request.files["file"]
    if file and allowed_file(file.filename):
        suffix = get_file_suffix(file.filename)
        filename = secure_filename(name + "." + suffix)
        file.save(TEASER_PATH.joinpath(filename))
        copyfile(TEASER_PATH.joinpath(filename), TEASER_BACKUP.joinpath(filename))

    return Response(status=200)

@bp.post('/api/v1/group/tags')
@flask_login.login_required
def group_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    db_wrapper.group_tags(cur, request.json["parent"], request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/split/tags')
@flask_login.login_required
def split_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    db_wrapper.split_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/merge/tags')
@flask_login.login_required
def merge_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    db_wrapper.merge_tags(cur, request.json["rows"])
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/add/evidence')
@flask_login.login_required
def add_evidence():
    cur = db.cursor()

    rows = request.json["rows"]
    for e in rows:

        if "filename" in e:
            name = e["filename"]
            e["filepath"] = None

            suff = [p.suffix for p in EVIDENCE_PATH.glob(name+".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name+suff

    db_wrapper.add_evidence(cur, rows)
    db.commit()

    return Response(status=200)


@bp.post('/api/v1/update/item/datatags')
@flask_login.login_required
def update_item_datatags():
    cur = db.cursor()
    db_wrapper.update_item_datatags(cur, request.json)
    db.commit()
    return Response(status=200)

@bp.post('/api/v1/start/codes/transition/old/<oldcode>/new/<newcode>')
@flask_login.login_required
def start_code_transition(oldcode, newcode):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    has_new = cur.execute("SELECT * FROM codes WHERE id = ?;", (newcode,)).fetchone()

    if not has_old or not has_new:
        print("codes missing for code transition")
        return Response(status=500)

    trans = db_wrapper.get_code_transitions_by_codes(cur, oldcode, newcode)

    if len(trans) > 0 and trans[0]["finished"] is None:
        return Response(status=200)
    elif len(trans) > 0 and trans[0]["finished"] is not None:
        print("code transition already finished")
        return Response(status=500)

    now = round(datetime.now(timezone.utc).timestamp() * 1000)

    cur.row_factory = db_wrapper.namedtuple_factory

    # try:
    db_wrapper.add_code_transitions(cur, [{ "old_code": oldcode, "new_code": newcode, "started": now }])
    db_wrapper.prepare_transition(cur, oldcode, newcode)
    db.commit()
    # except Exception as e:
    #     print("error preparing transition")
    #     print(str(e))
    #     return Response(status=500)

    return Response(status=200)

@bp.post('/api/v1/finalize/codes/transition/old/<oldcode>/new/<newcode>')
@flask_login.login_required
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