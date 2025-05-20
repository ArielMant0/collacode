import os
from base64 import b64decode
from pathlib import Path
from shutil import copyfile
from uuid import uuid4

import app.user_manager as user_manager
from app.calc import get_irr_score_tags, get_irr_score_items
import db_wrapper
import flask_login
import requests
import validators

from app import bp
from app.extensions import db, login_manager, lobby_manager
from app.open_library_api_loader import (
    search_openlibray_by_author,
    search_openlibray_by_isbn,
    search_openlibray_by_title,
)
from app.steam_api_loader import get_gamedata_from_id, get_gamedata_from_name
from app.open_library_api_loader import search_openlibray_by_author, search_openlibray_by_isbn, search_openlibray_by_title
from flask import Response, jsonify, request
from werkzeug.utils import secure_filename

EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "..", "dist", "evidence"
)
EVIDENCE_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "..", "public", "evidence"
)
TEASER_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "..", "dist", "teaser"
)
TEASER_BACKUP = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "..", "public", "teaser"
)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "mp4"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_suffix(filename):
    idx = filename.rfind(".")
    if idx > 0:
        return filename[idx + 1 :]
    return "png"

@login_manager.user_loader
def user_loader(user_id):
    return user_manager.get_user(user_id)


@bp.get("/api/v1/user_login")
def get_user_login():
    if flask_login.current_user and flask_login.current_user.is_authenticated:
        flask_login.confirm_login()
        return jsonify({"id": flask_login.current_user.id})

    return Response(status=401)

@bp.route("/api/v1/login", methods=["GET", "POST"])
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
            return jsonify({"id": user.id})
        else:
            return Response(status=403)

    return Response(status=404)


@bp.route("/api/v1/logout", methods=["GET", "POST"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return Response(status=200)


@bp.post("/api/v1/user_pwd")
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


@bp.get("/api/v1/lastupdate/dataset/<dataset>")
def get_last_update(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    return jsonify([dict(d) for d in db_wrapper.get_last_updates(cur, dataset)])

###################################################
## Data import
###################################################

@bp.get("/api/v1/import/steam/id/<steamid>")
def import_from_steam_id(steamid):
    result = get_gamedata_from_id(str(steamid))
    return jsonify({"data": [result]})


@bp.get("/api/v1/import/steam/name/<steamname>")
def import_from_steam_name(steamname):
    result = get_gamedata_from_name(steamname)
    return jsonify({"data": result})


@bp.get("/api/v1/import/openlibrary/isbn/<isbn>")
def import_from_openlibrary_isbn(isbn):
    result = search_openlibray_by_isbn(isbn)
    return jsonify({"data": result})


@bp.get("/api/v1/import/openlibrary/title/<title>")
def import_from_openlibrary_title(title):
    result = search_openlibray_by_title(str(title))
    return jsonify({"data": result})


@bp.get("/api/v1/import/openlibrary/author/<author>")
def import_from_openlibrary_author(author):
    result = search_openlibray_by_author(str(author))
    return jsonify({"data": result})

###################################################
## Inter-rater agreement
###################################################

@bp.get('/api/v1/irr/code/<code>/tags')
def get_irr_tags(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    ds = db_wrapper.get_dataset_by_code(cur, code)
    users = db_wrapper.get_users_by_dataset(cur, ds["id"])
    items = db_wrapper.get_items_merged_by_code(cur, code)
    tags = db_wrapper.get_tags_by_code(cur, code)
    tags = [t for t in tags if t["is_leaf"] == 1]
    scores = get_irr_score_tags(users, items, tags)
    return jsonify(scores)


@bp.get('/api/v1/irr/code/<code>/items')
def get_irr_items(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    ds = db_wrapper.get_dataset_by_code(cur, code)
    users = db_wrapper.get_users_by_dataset(cur, ds["id"])
    items = db_wrapper.get_items_merged_by_code(cur, code)
    tags = db_wrapper.get_tags_by_code(cur, code)
    tags = [t for t in tags if t["is_leaf"] == 1]
    scores = get_irr_score_items(users, items, tags)
    return jsonify(scores)

###################################################
## Games Lobby
###################################################

@bp.get('/api/v1/lobby/<game_id>/code/<code_id>')
def get_rooms_for_game(game_id, code_id):
    try:
        rooms = lobby_manager.get_rooms(game_id, int(code_id))
    except Exception as e:
        print(str(e))
        return Response("error getting room", status=500)

    return jsonify(rooms)

@bp.get('/api/v1/lobby/<game_id>/room/<room_id>')
def get_room(game_id, room_id):
    try:
        room = lobby_manager.get_room(game_id, room_id)
        if room is None:
            return Response("could not find room", status=500)
    except Exception as e:
        print(str(e))
        return Response("error getting room", status=500)

    return jsonify(room)

@bp.post('/api/v1/lobby/<game_id>/open')
def open_room(game_id):

    if "id" not in request.json:
        return Response("missing room id", status=500)
    if "code_id" not in request.json:
        return Response("missing room id", status=500)
    if "name" not in request.json:
        return Response("missing player name", status=500)

    id = request.json["id"]
    code_id = int(request.json["code_id"])
    name = request.json["name"]
    data = request.json["data"] if "data" in request.json else None

    try:
        room = lobby_manager.open(game_id, code_id, id, name, data)
        if room is None:
            return Response("could not open room", status=500)
    except Exception as e:
        print(str(e))
        return Response("error opening room", status=500)

    return jsonify(room)

@bp.post('/api/v1/lobby/<game_id>/close')
def close_room(game_id):

    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=500)

    try:
        room_id = request.json["room_id"]
        lobby_manager.close(game_id, room_id)
    except Exception as e:
        print(str(e))
        return Response("error closing room", status=500)

    return Response("okay", status=200)

@bp.post('/api/v1/lobby/<game_id>/update')
def update_room(game_id):
    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=500)

    room_id = request.json["room_id"]
    try:
        lobby_manager.update_room(game_id, room_id)
    except Exception as e:
        print(str(e))
        return Response("error updating room", status=500)

    return Response("okay", status=200)

@bp.post('/api/v1/lobby/<game_id>/join')
def join_room(game_id):

    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=500)
    if "id" not in request.json:
        print("missing player id")
        return Response("missing player id", status=500)
    if "name" not in request.json:
        print("missing player name")
        return Response("missing player name", status=500)

    room_id = request.json["room_id"]
    id = request.json["id"]
    name = request.json["name"]

    try:
        room = lobby_manager.join(game_id, room_id, id, name)
        if room is None:
            return Response("could not join room", status=500)
    except Exception as e:
        print(str(e))
        return Response("error joining room", status=500)

    return jsonify(room)

@bp.post('/api/v1/lobby/<game_id>/leave')
def leave_room(game_id):

    if "room_id" not in request.json:
        return Response("missing room id", status=500)
    if "id" not in request.json:
        return Response("missing player id", status=500)

    room_id = request.json["room_id"]
    id = request.json["id"]

    try:
        lobby_manager.leave(game_id, room_id, id)
    except Exception as e:
        print(str(e))
        return Response("error leaving room", status=500)

    return Response("okay", status=200)


###################################################
## Games Score Data
###################################################

@bp.get('/api/v1/game_scores/code/<code>')
def get_game_scores(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_by_code(cur, code)
    return jsonify(res)


@bp.get('/api/v1/game_scores_items/code/<code>')
def get_game_scores_items(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_items_by_code(cur, code)
    return jsonify(res)


@bp.get('/api/v1/game_scores_tags/code/<code>')
def get_game_scores_tags(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_tags_by_code(cur, code)
    return jsonify(res)


@bp.post("/api/v1/add/game_scores")
def add_game_scores():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/game_scores_items")
def add_game_scores_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores_items(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores items", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/game_scores_tags")
def add_game_scores_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores tags", status=500)

    return Response(status=200)

###################################################
## GET Data
###################################################

@bp.get("/api/v1/datasets")
def get_datasets():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    datasets = db_wrapper.get_datasets(cur)
    return jsonify([dict(d) for d in datasets])


@bp.get("/api/v1/items/dataset/<dataset>")
def get_items_data(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_items_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/item_expertise/dataset/<dataset>")
def get_item_expertise(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_item_expertise_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/users")
def get_users():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_users(cur)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/users/dataset/<dataset>")
def get_users_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_users_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/codes/dataset/<dataset>")
def get_codes_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_codes_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/tags/dataset/<dataset>")
def get_tags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/tags/code/<code>")
def get_tags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_code(cur, code)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/datatags/dataset/<dataset>")
def get_datatags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/datatags/code/<code>")
def get_datatags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_code(cur, code)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/datatags/tag/<tag>")
def get_datatags_tag(tag):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_tag(cur, tag)
    return jsonify([dict(d) for d in data])


@bp.get("/api/v1/evidence/dataset/<dataset>")
def get_evidence_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in evidence])


@bp.get("/api/v1/evidence/code/<code>")
def get_evidence_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    return jsonify([dict(d) for d in evidence])


@bp.get("/api/v1/tag_assignments/dataset/<dataset>")
def get_tag_assignments_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in tas])


@bp.get("/api/v1/tag_assignments/code/<code>")
def get_tag_assignments(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_old_code(cur, code)
    return jsonify([dict(d) for d in tas])


@bp.get("/api/v1/tag_assignments/old/<old_code>/new/<new_code>")
def get_tag_assignments_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_codes(cur, old_code, new_code)
    return jsonify([dict(d) for d in tas])


@bp.get("/api/v1/code_transitions/dataset/<dataset>")
def get_code_transitions(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/api/v1/code_transitions/code/<code>")
def get_code_transitions_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_old_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/code_transitions/old/<old_code>/new/<new_code>")
def get_code_transitions_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_codes(cur, old_code, new_code)
    return jsonify(result)


@bp.get("/api/v1/meta_groups/code/<code>")
def get_meta_groups_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_groups_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_items/code/<code>")
def get_mitems_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_items_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_categories/code/<code>")
def get_meta_cats_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_categories_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_agreements/code/<code>")
def get_meta_agree_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_agreements_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_cat_connections/code/<code>")
def get_meta_cat_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_cat_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_tag_connections/code/<code>")
def get_meta_tag_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_tag_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/meta_ev_connections/code/<code>")
def get_meta_ev_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_ev_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/api/v1/objections/code/<code>")
def get_objections_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    try:
        result = db_wrapper.get_objections_by_code(cur, code)
    except Exception as e:
        print(str(e))
        return Response("error getting objections", status=500)

    return jsonify(result)

###################################################
## ADD Data
###################################################

@bp.post("/api/v1/add/dataset")
@flask_login.login_required
def add_dataset():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    db_wrapper.add_dataset(cur, request.json)
    db.commit()
    return Response(status=200)


@bp.post("/api/v1/import")
@flask_login.login_required
def upload_data():
    cur = db.cursor()

    body = request.json

    if "dataset" not in body and "dataset_id" not in body:
        print("missing dataset")
        return Response("missing dataset", status=500)

    existing = "dataset_id" in body and body["dataset_id"] is not None

    if existing and "code_id" not in body:
        print("missing code")
        return Response("missing code", status=500)

    if "users" not in body:
        print("missing users")
        return Response("missing users", status=500)

    if "datatags" in body and "dt_user" not in body:
        print("missing user for datatags")
        return Response("missing user for user tags", status=500)

    if "items" not in body and "tags" not in body and "datatags" not in body:
        print("import: missing data")
        return Response("missing data", status=500)

    cur.row_factory = db_wrapper.namedtuple_factory

    user_id = None

    if existing:
        ds_id = int(body["dataset_id"])
        code_id = int(body["code_id"])

        try:
            for user in body["users"]:
                if "id" in user and db_wrapper.has_user_by_id(cur, user["id"]):
                    if not db_wrapper.has_project_user_by_id(cur, ds_id, user["id"]):
                        db_wrapper.add_users_to_project(cur, ds_id, [user["id"]])
                    if "dt_user" in body and user["name"] == body["dt_user"]:
                        user_id = int(user["id"])
                elif "name" in user and not db_wrapper.has_user_by_name(cur, user["name"]):
                    uid = db_wrapper.add_user_return_id(cur, user)
                    db_wrapper.add_users_to_project(cur, ds_id, [uid])
                    if "dt_user" in body and user["name"] == body["dt_user"]:
                        user_id = uid
                else:
                    print(str(e))
                    return Response("missing user name", status=500)

        except ValueError as e:
            print(str(e))
            return Response("error importing data", status=500)

    else:
        dataset = body["dataset"]

        try:
            ds_id = db_wrapper.add_dataset(cur, dataset)
            print("created dataset", dataset["name"])

            code_id = db_wrapper.get_codes_by_dataset(cur, ds_id)[0].id
            du = db_wrapper.get_users_by_dataset(cur, ds_id)
            if "dt_user" in body:
                user_id = [u.id for u in du if u.name == body["dt_user"]][0]
            else:
                user_id = du[0].id

        except ValueError as e:
            print(str(e))
            return Response("error importing data", status=500)

    try:
        now = db_wrapper.get_millis()

        tids = {}
        # add tags
        if "tags" in body:
            tags = body["tags"]
            changes = True

            while changes:
                changes = False
                for t in tags:
                    if t["id"] in tids or (t["parent"] > 0 and t["parent"] not in tids):
                        continue

                    t["code_id"] = code_id
                    t["created_by"] = user_id
                    t["created"] = now
                    copy = t.copy()
                    if t["parent"] > 0:
                        copy["parent"] = tids[t["parent"]]
                    else:
                        del copy["parent"]

                    tids[t["id"]] = db_wrapper.add_tag_return_id(cur, copy)
                    changes = True

            print(f"added {len(tags)} tags")
            db_wrapper.update_tags_is_leaf(cur, list(tids.values()))
        else:
            indb = db_wrapper.get_tags_by_code(cur, code_id)
            for i, tag in enumerate(indb):
                tids[(i+1)] = tag.id

        iids = {}
        # add items
        if "items" in body:
            items = body["items"]

            for d in items:

                d["dataset_id"] = ds_id

                if "teaser" in d and d["teaser"] is not None and len(d["teaser"]) > 0:
                    if validators.url(d["teaser"]):
                        url = d["teaser"]
                        response = requests.get(url)
                        if response.status_code == 200:
                            suff = get_file_suffix(url.split("/")[-1])
                            name = str(uuid4())
                            filename = name + "." + suff
                            filepath = TEASER_PATH.joinpath(filename)
                            with open(filepath, "wb") as fp:
                                fp.write(response.content)
                            copyfile(filepath, TEASER_BACKUP.joinpath(filename))
                            d["teaser"] = filename

                iids[d["id"]] = db_wrapper.add_item_return_id(cur, d)

            print(f"added {len(items)} items")
        else:
            indb = db_wrapper.get_items_by_dataset(cur, ds_id)
            for i, item in enumerate(indb):
                iids[(i+1)] = item.id

        # add datatags
        if "datatags" in body and user_id is not None:
            dts = body["datatags"]
            rows = []
            for dt in dts:
                if dt["tag_id"] in tids and dt["item_id"] in iids:
                    dt["code_id"] = code_id
                    dt["created_by"] = user_id
                    dt["created"] = now
                    dt["tag_id"] = tids[dt["tag_id"]]
                    dt["item_id"] = iids[dt["item_id"]]
                    rows.append(dt)

            db_wrapper.add_datatags(cur, rows)
            print(f"added {len(rows)} datatags")

        db.commit()

    except ValueError as e:
        print(str(e))
        return Response("error importing data", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/items")
@flask_login.login_required
def add_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

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
            suff = [p.suffix for p in TEASER_PATH.glob(name + ".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["teaser"] = name + suff

    try:
        db_wrapper.add_items(cur, request.json["dataset"], rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding items", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/item_expertise")
@flask_login.login_required
def add_item_expertise():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_item_expertise(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding item expertise", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/codes")
@flask_login.login_required
def add_codes():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_codes(cur, request.json["dataset"], request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding codes", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/tags")
@flask_login.login_required
def add_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tags", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/datatags")
@flask_login.login_required
def add_datatags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_datatags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding datatags", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/tags/assign")
@flask_login.login_required
def add_tags_for_assignment():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    try:
        db_wrapper.add_tags_for_assignment(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tags for assignment", status=500)
    return Response(status=200)


@bp.post("/api/v1/add/tag_assignments")
@flask_login.login_required
def add_tag_assignments():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_tag_assignments(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tag assignments", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/meta_items")
@flask_login.login_required
def add_meta_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_items(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta items", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/meta_agreements")
@flask_login.login_required
def add_meta_agreements():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_agreements(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta agreements", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/meta_categories")
@flask_login.login_required
def add_meta_categories():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_categories(
            cur, request.json["dataset"], request.json["code"], request.json["rows"]
        )
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta categories", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/objections")
@flask_login.login_required
def add_objections():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_objections(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding objections", status=500)

    return Response(status=200)

###################################################
## UPDATE Data
###################################################

@bp.post("/api/v1/update/codes")
@flask_login.login_required
def update_codes():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_codes(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating codes", status=500)
    return Response(status=200)


@bp.post("/api/v1/update/tags")
@flask_login.login_required
def update_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating tags", status=500)
    return Response(status=200)


@bp.post("/api/v1/update/item_expertise")
@flask_login.login_required
def update_item_expertise():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_item_expertise(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating item expertise", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/items")
@flask_login.login_required
def update_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    rows = request.json["rows"]
    for e in rows:
        name = e.get("teaserName", "")
        filepath = e.get("teaser", "")

        if name:
            suff = [p.suffix for p in TEASER_PATH.glob(name + ".*")][0]
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

            e["teaser"] = name + suff

    try:
        db_wrapper.update_items(cur, rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating items", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/evidence")
@flask_login.login_required
def update_evidence():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    rows = request.json["rows"]
    for e in rows:
        name = e.get("filename", "")

        if name:
            suff = [p.suffix for p in EVIDENCE_PATH.glob(name + ".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name + suff

    try:
        db_wrapper.update_evidence(cur, request.json["rows"], EVIDENCE_PATH, EVIDENCE_BACKUP)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating evidence", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/tag_assignments")
@flask_login.login_required
def update_tag_assignments():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    try:
        db_wrapper.update_tag_assignments(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating tag assignments", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/meta_groups")
@flask_login.login_required
def update_meta_groups():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    try:
        db_wrapper.update_meta_groups(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta groups", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/meta_items")
@flask_login.login_required
def update_meta_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_items(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta items", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/meta_agreements")
@flask_login.login_required
def update_meta_agreements():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_agreements(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta agreements", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/meta_categories")
@flask_login.login_required
def update_meta_categories():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_categories(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta categories", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/objections")
@flask_login.login_required
def update_objections():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_objections(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating objections", status=500)

    return Response(status=200)

###################################################
## DELETE Data
###################################################

@bp.post("/api/v1/delete/items")
@flask_login.login_required
def delete_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_items(cur, request.json["ids"], TEASER_PATH, TEASER_BACKUP)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting items", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/tags")
@flask_login.login_required
def delete_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_tags(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting tags", status=500)
    return Response(status=200)


@bp.post("/api/v1/delete/item_expertise")
@flask_login.login_required
def delete_item_expertise():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_item_expertise(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting item expertise", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/datatags")
@flask_login.login_required
def delete_datatags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_datatags(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting datatags", status=500)
    return Response(status=200)


@bp.post("/api/v1/delete/evidence")
@flask_login.login_required
def delete_evidence():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_evidence(cur, request.json["ids"], EVIDENCE_PATH, EVIDENCE_BACKUP)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting evidence", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/tag_assignments")
@flask_login.login_required
def delete_tag_assignments():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_tag_assignments(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting tag assignments", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/code_transitions")
@flask_login.login_required
def delete_code_transitions():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_code_transitions(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting code transtion", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_items")
@flask_login.login_required
def delete_meta_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_items(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta items", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_cat_conns")
@flask_login.login_required
def delete_meta_cat_conns():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_cat_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta category connections", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_tag_conns")
@flask_login.login_required
def delete_meta_tag_conns():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_tag_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta tag connections", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_ev_conns")
@flask_login.login_required
def delete_meta_ev_conns():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_ev_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta evidence connections", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_agreements")
@flask_login.login_required
def delete_meta_agreements():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_agreements(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta agreements", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/meta_categories")
@flask_login.login_required
def delete_meta_categories():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_categories(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta categories", status=500)

    return Response(status=200)


@bp.post("/api/v1/delete/objections")
@flask_login.login_required
def delete_objections():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_objections(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting objections", status=500)

    return Response(status=200)


###################################################
## MISC
###################################################

@bp.post("/api/v1/image/evidence/<name>")
@flask_login.login_required
def upload_image_evidence(name):
    if "file" not in request.files:
        return Response("missing evidence image", status=500)

    try:
        file = request.files["file"]
        if file and allowed_file(file.filename):
            suffix = get_file_suffix(file.filename)
            filename = secure_filename(name + "." + suffix)
            file.save(EVIDENCE_PATH.joinpath(filename))
            copyfile(EVIDENCE_PATH.joinpath(filename), EVIDENCE_BACKUP.joinpath(filename))
    except Exception as e:
        print(str(e))
        return Response("error uploading evidence image", status=500)

    return Response(status=200)


@bp.post("/api/v1/image/teaser/<name>")
@flask_login.login_required
def upload_image_teaser(name):
    if "file" not in request.files:
        return Response("missing teaser image", status=500)

    try:
        file = request.files["file"]
        if file and allowed_file(file.filename):
            suffix = get_file_suffix(file.filename)
            filename = secure_filename(name + "." + suffix)
            file.save(TEASER_PATH.joinpath(filename))
            copyfile(TEASER_PATH.joinpath(filename), TEASER_BACKUP.joinpath(filename))
    except Exception as e:
        print(str(e))
        return Response("error uploading teaser image", status=500)

    return Response(status=200)

@bp.post("/api/v1/image/teasers")
@flask_login.login_required
def upload_image_teasers():

    for name, file in request.files.items():
        try:
            if file and allowed_file(file.filename):
                suffix = get_file_suffix(file.filename)
                filename = secure_filename(name + "." + suffix)
                file.save(TEASER_PATH.joinpath(filename))
                copyfile(TEASER_PATH.joinpath(filename), TEASER_BACKUP.joinpath(filename))
        except Exception as e:
            print(str(e))
            return Response("error uploading teaser image", status=500)

    return Response(status=200)

@bp.post("/api/v1/group/tags")
@flask_login.login_required
def group_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.group_tags(cur, request.json["parent"], request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error grouping tags", status=500)

    return Response(status=200)


@bp.post("/api/v1/split/tags")
@flask_login.login_required
def split_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.split_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error splitting tags", status=500)

    return Response(status=200)


@bp.post("/api/v1/merge/tags")
@flask_login.login_required
def merge_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.merge_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error mergin tags", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/evidence")
@flask_login.login_required
def add_evidence():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    rows = request.json["rows"]
    for e in rows:

        if "filename" in e:
            name = e["filename"]
            e["filepath"] = None

            suff = [p.suffix for p in EVIDENCE_PATH.glob(name + ".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name + suff

    try:
        db_wrapper.add_evidence(cur, rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding evidence", status=500)

    return Response(status=200)


@bp.post("/api/v1/add/meta_cat_conns")
@flask_login.login_required
def add_meta_cat_conns():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_cat_conns(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta category connections", status=500)

    return Response(status=200)


@bp.post("/api/v1/update/item/datatags")
@flask_login.login_required
def update_item_datatags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_item_datatags(cur, request.json)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating item datatags", status=500)

    return Response(status=200)


@bp.post("/api/v1/start/code_transition")
@flask_login.login_required
def start_code_transition():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    oldcode = request.json["old_code"]
    new_code_data = request.json["new_code"]

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    if not has_old:
        return Response("missing old code", status=500)

    trans = cur.execute(
        "SELECT * FROM code_transitions WHERE old_code = ?;", (oldcode,)
    ).fetchall()
    if len(trans) > 0:
        return Response("transition for this code already exists", status=500)

    try:
        newcode = db_wrapper.add_code_return_id(cur, has_old.dataset_id, new_code_data)
    except Exception as e:
        print(str(e))
        return Response("error adding new code", status=500)

    try:
        now = db_wrapper.get_millis()
        db_wrapper.add_code_transitions(
            cur, [{"old_code": oldcode, "new_code": newcode, "started": now}]
        )
        db_wrapper.prepare_transition(cur, oldcode, newcode)
        db.commit()
    except Exception as e:
        print("error preparing transition")
        print(str(e))
        return Response("error preparing transition", status=500)

    return Response(status=200)
