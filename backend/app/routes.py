import os
from base64 import b64decode
from datetime import datetime, timezone
from pathlib import Path

import app.user_manager as user_manager
from app.calc import get_irr_score_tags, get_irr_score_items
import config
import db_wrapper
import flask_login
import requests
from sklearn.cluster import HDBSCAN, DBSCAN, AgglomerativeClustering, KMeans, MeanShift
import validators

from app import bp
from app import crowd_wrapper as cw
from app.extensions import db, cdb, login_manager, lobby_manager
from app.open_library_api_loader import (
    search_openlibray_by_author,
    search_openlibray_by_isbn,
    search_openlibray_by_title,
)
from app.steam_api_loader import get_gamedata_from_id, get_gamedata_from_name
from app.open_library_api_loader import search_openlibray_by_author, search_openlibray_by_isbn, search_openlibray_by_title
from flask import Response, jsonify, request, send_file
from werkzeug.utils import secure_filename

EVIDENCE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", config.EVIDENCE_PATH
).resolve()
TEASER_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", config.TEASER_PATH
).resolve()

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "svg", "mp4", "mov", "mkv"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_suffix(filename):
    idx = filename.rfind(".")
    if idx > 0:
        return filename[idx + 1 :]
    return "png"

def get_file_prefix():
    now = datetime.now(timezone.utc)
    return now.strftime("%Y%m%d%H%M%S_")

def save_teaser_from_url(url, dspath):
    response = requests.get(url)
    if response.status_code == 200:
        base_name = url.split("/")[-1]
        suff = get_file_suffix(base_name)

        idx = base_name.rfind(".")
        if idx > 0:
            base_name = base_name[0:idx]

        name = get_file_prefix() + base_name

        if not TEASER_PATH.joinpath(dspath).exists():
            TEASER_PATH.joinpath(dspath).mkdir(parents=True, exist_ok=True)

        fp = TEASER_PATH.joinpath(dspath, name + "." + suff)
        base = fp.stem
        final = base
        counter = 1
        while fp.exists():
            final = f"{base}_{counter}"
            fp = fp.with_stem(final)
            counter += 1

        filename = final + "." + suff
        filepath = TEASER_PATH.joinpath(dspath, filename)
        with open(filepath, "wb") as fp:
            fp.write(response.content)

        return filename

    return None

def save_teaser(file, name, dspath):
    suffix = get_file_suffix(file.filename)
    filename = secure_filename(name + "." + suffix)

    if not TEASER_PATH.joinpath(dspath).exists():
        TEASER_PATH.joinpath(dspath).mkdir(parents=True, exist_ok=True)

    tp = TEASER_PATH.joinpath(dspath, filename)
    base = get_file_prefix() + tp.stem
    final = base
    counter = 1

    while tp.exists():
        final = f"{base}_{counter}"
        tp = tp.with_stem(final)
        counter += 1

    final_file = final + "." + suffix

    file.save(TEASER_PATH.joinpath(dspath, final_file))

    return final_file

def save_evidence(file, name, dspath):
    suffix = get_file_suffix(file.filename)
    filename = secure_filename(name + "." + suffix)

    if not EVIDENCE_PATH.joinpath(dspath).exists():
        EVIDENCE_PATH.joinpath(dspath).mkdir(parents=True, exist_ok=True)

    ep = EVIDENCE_PATH.joinpath(dspath, filename)
    base = get_file_prefix() + ep.stem
    final = base
    counter = 1
    while ep.exists():
        final = f"{base}_{counter}"
        ep = ep.with_stem(final)
        counter += 1

    final_file = final + "." + suffix
    file.save(EVIDENCE_PATH.joinpath(dspath, final_file))

    return final_file


@login_manager.user_loader
def user_loader(user_id):
    return user_manager.get_user(user_id)


@bp.get("/user_login")
def get_user_login():
    if flask_login.current_user and flask_login.current_user.is_authenticated:
        flask_login.confirm_login()
        return jsonify({ "id": flask_login.current_user.id })

    return Response(status=401)

@bp.route("/login", methods=["GET", "POST"])
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


@bp.route("/logout", methods=["GET", "POST"])
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return Response(status=200)


@bp.post("/user_pwd")
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


@bp.get("/lastupdate/dataset/<int:dataset>")
def get_last_update(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = [dict(d) for d in db_wrapper.get_last_updates(cur, dataset)]
    return jsonify(result)


# @bp.get("/media/<folder>/<int:dataset>/<path>")
# def get_media(folder, dataset, path):
#     p = None
#     if folder == "teaser":
#         p = TEASER_PATH.joinpath(dataset, path)
#     elif folder == "evidence":
#         p = EVIDENCE_PATH.joinpath(dataset, path)

#     if p is not None and p.exists():
#         try:
#             return send_file(p)
#         except Exception as e:
#             print(str(e))
#             return Response(status=500)

#     return Response(status=404)

###################################################
## Crowd Similarity Data
###################################################

def get_prolific_links():
    return {
        "linkSuccess": config.PROLIFIC_LINK_SUCCESS,
        "codeSuccess": config.PROLIFIC_CODE_SUCCES,
        "linkFail": config.PROLIFIC_LINK_FAIL,
        "codeFail": config.PROLIFIC_CODE_FAIL,
        "linkSoftlock": config.PROLIFIC_LINK_SOFTLOCK,
        "codeSoftlock": config.PROLIFIC_CODE_SOFTLOCK,
    }


@bp.get("/crowd/prolific/link")
def get_crowd_links():
    return jsonify(get_prolific_links())


@bp.post("/crowd/prolific/submitted")
def set_prolific_submitted():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # get required client information
    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)

    try:
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if client is None:
            return Response("client does not exist", status=500)

        cw.set_crowd_worker_submitted(cur, client)
        cdb.commit()
    except Exception as e:
        print(str(e))
        return Response("error getting client data", status=500)

    return Response(status=200)

@bp.get("/crowd/analysis/meta")
def get_crowd_analysis_meta():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    curc = cdb.cursor()
    curc.row_factory = db_wrapper.dict_factory
    dsid = 1

    # get code
    codes = db_wrapper.get_codes_by_dataset(cur, dsid)
    if codes is None or len(codes) == 0:
        return Response("missing codes", status=500)

    code = codes[-1]["id"]
    dataset = db_wrapper.get_dataset_by_code(cur, code)

    if config.DEBUG and config.CROWD_NO_AUTH:
        return jsonify({
            "dataset": dataset,
            "code": code,
            "excludedTags": cw.get_excluded_tags(dsid),
        })

    return jsonify({})


@bp.get("/crowd/analysis/items")
def get_crowd_analysis_items():
    curc = cdb.cursor()
    curc.row_factory = db_wrapper.dict_factory

    dsid = 1

    if config.DEBUG and config.CROWD_NO_AUTH:
        item_ids = cw.get_available_items(dsid)
        return jsonify({
            "items": item_ids,
            "itemCounts": cw.get_submission_counts_by_targets(curc, item_ids, False),
        })

    return jsonify([])


@bp.get("/crowd/analysis/clients")
def get_crowd_analysis_clients():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    dsid = 1
    clients = []

    if config.DEBUG and config.CROWD_NO_AUTH:
        clients = cw.get_clients(cur)
        for c in clients:
            c["ratings"] = cw.get_ratings_by_client(cur, c["id"])
            c["feedback"] = cw.get_feedback_by_client(cur, c["id"])
            c["submissions"] = cw.get_submissions_by_client_dataset(cur, c["id"], dsid, True)

    return jsonify(clients)


@bp.get("/crowd/analysis/submissions")
def get_crowd_analysis_submissions():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    dsid = 1

    if config.DEBUG and config.CROWD_NO_AUTH:
        return jsonify(cw.get_submissions_by_dataset(cur, dsid, True))

    return jsonify([])


@bp.get("/crowd/analysis/ratings")
def get_ratings_analysis():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    if config.DEBUG and config.CROWD_NO_AUTH:
        try:
            return jsonify(cw.get_ratings(cur))
        except Exception as e:
            return Response(str(e), status=500)

    return jsonify([])


@bp.get("/crowd")
def get_crowd_meta_info():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    curc = cdb.cursor()
    curc.row_factory = db_wrapper.dict_factory

    dsid = 1

    # get code
    codes = db_wrapper.get_codes_by_dataset(cur, dsid)
    if codes is None or len(codes) == 0:
        return Response("missing codes", status=500)

    code = codes[-1]["id"]
    dataset = db_wrapper.get_dataset_by_code(cur, code)

    # get required client information
    cid = request.args.get('client', None)
    if cid is not None:
        try:
            cid = int(cid)
        except:
            print(cid)
            cid = None

    guid = request.args.get('guid', None)
    ip = request.args.get('ip', None)
    user_src = request.args.get('source', None)
    cw_id = request.args.get('cwId', None)

    info = {
        "dataset": dataset,
        "code": code,
        "excludedTags": cw.get_excluded_tags(dsid),
        "client": None,
        "guid": None,
        "cwId": None,
        "source": None,
        "cwSubmitted": False,
        "submissions": 0,
        "blocked": False,
        "methodCounts": None,
        "cwLinks": get_prolific_links(),
    }

    client = None

    try:
        client = cw.get_client_update(curc, cid, guid, user_src, ip, cw_id)
        if client is None:
            # new user - store client information
            client = cw.add_client_info(curc, guid, user_src, ip, cw_id)
            if client is None:
                print("could not create new client")
                return Response("could not create new client", status=500)

        # general client data
        info["client"] = client["id"]
        info["guid"] = client["guid"]
        info["method"] = client["method"]
        info["submissions"] = cw.get_submissions_count_by_client_dataset(curc, client["id"], dsid)
        info["source"] = client["source"]
        info["methodCounts"] = cw.get_game_counts_by_client(curc, client["id"])

        if cw.is_client_blocked(client):
            info["blocked"] = True

        # crowd worker data
        if client["cwId"] is not None:
            info["cwId"] = client["cwId"]
            info["cwSubmitted"] = client["cwSubmitted"] == 1
            if client["cwSubmitted"] == 1:
                info["method"] = 0

        cdb.commit()

    except Exception as e:
        print(str(e))
        return Response("error getting client data", status=500)

    return jsonify(info)

@bp.get("/crowd/items")
def get_crowd_items():
    curc = cdb.cursor()
    curc.row_factory = db_wrapper.dict_factory

    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    dsid = 1

    # get required client information
    cid = request.args.get('client', None)
    if cid is not None:
        try:
            cid = int(cid)
        except:
            print(cid)
            cid = None

    guid = request.args.get('guid', None)
    ip = request.args.get('ip', None)
    user_src = request.args.get('source', None)
    cw_id = request.args.get('cwId', None)

    if cid is None or guid is None:
        return Response("missing identification", status=400)

    # get all item ids
    item_ids = cw.get_available_items(dsid)
    all_item_ids = [d["id"] for d in db_wrapper.get_items_by_dataset(cur, dsid)]

    data = {
        "itemsLeft": [],
        "itemsDone": [],
        "itemsGone": [],
        "itemCounts": cw.get_submission_counts_by_targets(curc, item_ids, False),
    }

    try:
        client = cw.get_client_update(curc, cid, guid, user_src, ip, cw_id)

        if client is None:
            return Response("invalid client id", status=500)

        blocked = cw.is_client_blocked(client)
        done, invalid = cw.get_client_items_by_dataset(curc, client["id"], dsid)

        use_all_items = True

        if client["cwId"] is not None:
            data["cwId"] = client["cwId"]
            data["cwSubmitted"] = client["cwSubmitted"] == 1
            if client["cwSubmitted"] == 1:
                data["method"] = 0
            else:
                use_all_items = False

        data["blocked"] = blocked
        data["itemsDone"] = list(done) if use_all_items else [id for id in item_ids if id in done]
        data["method"] = client["method"]
        data["submissions"] = cw.get_submissions_count_by_client_dataset(curc, client["id"], dsid)
        data["source"] = client["source"]
        data["methodCounts"] = cw.get_game_counts_by_client(curc, client["id"])
        data["methodPerItem"] = cw.get_game_per_item_by_client(curc, client["id"])

        if not blocked:
            # filter data by this user's existing submissions
            data["itemsLeft"] = [id for id in item_ids if id not in done and id not in invalid]
            data["itemsGone"] = list(invalid) if use_all_items else [id for id in item_ids if id in invalid]
            # check if the number of submssions exceeds the limit
            if client["cwId"] is not None:
                blocked = blocked or cw.is_crowd_worker_done(curc, client, dsid)

        if blocked:
            data["itemsLeft"] = []
            data["itemsGone"] = all_item_ids if use_all_items else [id for id in item_ids if id not in done]

    except Exception as e:
        print(str(e))
        return Response("error getting client items", status=500)

    return jsonify(data)


@bp.post("/crowd/interactions")
def add_interaction_logs():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    cid = request.json.get('client', None)
    rows = request.json.get('rows', None)

    if cid is None:
        return Response("missing identification", status=400)

    if rows is None:
        return Response(status=200)

    try:
        cw.add_interaction_logs(cur, cid, rows)
        cdb.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding interaction log", status=500)

    return Response(status=200)


@bp.get("/crowd/comprehension")
def get_crowd_comprehension():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # get required client information
    item_id = request.args.get('itemId', None)
    if item_id is None:
        return Response("missing item data", status=400)

    item_id = int(item_id)

    # get the comprehension check data for this item id
    questions = cw.get_comprehension_check(item_id, True)
    if questions is not None:
        return jsonify(questions)

    return jsonify([])


@bp.post("/crowd/comprehension/test")
def test_crowd_comprehension():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # comprehension data
    item_id = request.json.get('itemId', None)
    answers = request.json.get('answers', None)

    # get required client information
    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)
    game_id = request.json.get('gameId', None)

    dsid = 1

    if item_id is None or answers is None or guid is None or game_id is None:
        return Response("missing data", status=400)

    try:
        passed = cw.test_comprehension_check(item_id, answers)
        if not passed:
            client = cw.get_client(cur, cid, guid, ip, cw_id)
            if not client:
                Response("could not find matching client", status=500)

            cw.update_client_comprehension_fails(cur, client["id"])
            # add an empty submission so that they cannot do the same item again
            cw.add_blocked_item(
                cur,
                client["id"],
                item_id,
                {
                    "target_id": item_id,
                    "game_id": game_id,
                    "dataset_id": dsid
                },
                "failed comprehension check"
            )
            cdb.commit()
            db_wrapper.log_update(db.cursor(), "crowd", dsid)
            db.commit()
            return jsonify({ "passed": False })

    except Exception as e:
        print(str(e))
        return Response("error evaluating comprehension check", status=500)

    return jsonify({ "passed": True })


@bp.post("/crowd/attention/fail")
def add_crowd_attention_fail():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # get required client information
    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)

    game_id = request.json.get('gameId', None)
    item_id = request.json.get('itemId', None)

    if (cid is None and guid is None) or item_id is None or game_id is None:
        return Response("missing data", status=400)

    dsid = 1

    try:
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if not client:
            Response("could not find matching client", status=500)

        cw.update_client_attention_fails(cur, client["id"])
        # add an empty submission so that they cannot do the same item again
        cw.add_blocked_item(
            cur,
            client["id"],
            item_id,
            {
                "target_id": item_id,
                "game_id": game_id,
                "dataset_id": dsid
            },
            "failed attention check"
        )
        cdb.commit()
        db_wrapper.log_update(db.cursor(), "crowd", dsid)
        db.commit()

    except Exception as e:
        print(str(e))
        return Response("error adding attention fail", status=500)

    return Response(status=200)


@bp.post("/crowd/feedback/add")
def add_feedback():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)

    if cid is None:
        return Response("missing client data", status=400)

    text = request.json.get('text', None)
    game_id = request.json.get('game_id', None)

    if text is None or game_id is None:
        return Response("missing feedback data", status=400)

    try:
        # get the matching client
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if client is None:
            return Response("no matching client found", status=500)

        cw.add_feedback(cur, client["id"], game_id, text)
        cdb.commit()
    except Exception as e:
        print(str(e))
        return Response("feedback already exists", status=500)

    return Response(status=200)


@bp.get("/crowd/ratings/stats")
def get_ratings_stats():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    try:
        return jsonify(cw.get_ratings_counts(cur))
    except Exception as e:
        return Response(str(e), status=500)


@bp.get("/crowd/ratings")
def get_client_ratings():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    cid = request.args.get('client', None)
    guid = request.args.get('guid', None)
    ip = request.args.get('ip', None)
    cw_id = request.args.get('cwId', None)

    try:
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if client is None:
            return Response("no matching client found", status=500)

        ratings = cw.get_ratings_by_client(cur, client["id"])
        return jsonify(ratings)
    except Exception as e:
        return Response(str(e), status=500)


@bp.post("/crowd/ratings/add")
def add_client_ratings():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)

    ratings = request.json["ratings"]

    try:
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if client is None:
            return Response("no matching client found", status=500)

        cw.add_ratings(cur, client["id"], ratings)
        cdb.commit()
    except Exception as e:
        return Response(str(e), status=500)

    return Response(status=200)


@bp.get("/crowd/client/method_counts")
def get_client_method_counts():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # get required client information
    cid = request.args.get('client', None)
    if cid is not None:
        try:
            cid = int(cid)
        except:
            print(cid)
            cid = None

    guid = request.args.get('guid', None)
    if cid is None or guid is None:
        return Response("missing client data", status=400)

    try:
        return jsonify(cw.get_game_counts_by_client(cur, cid))
    except Exception as e:
        print(str(e))
        return Response(str(e), status=500)


@bp.get("/crowd/client/status")
def get_client_status():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    # get required client information
    cid = request.args.get('client', None)
    if cid is not None:
        try:
            cid = int(cid)
        except:
            print(cid)
            cid = None

    guid = request.args.get('guid', None)
    if cid is None or guid is None:
        return Response("missing client data", status=200)

    try:
        client = cw.get_client_by_id(cur, cid)
        if client is not None:
            return Response("client does note exist", status=200)

        # check if this client should be blocked
        if cw.is_client_blocked(client):
            return Response("client blocked due to suspicious activity", status=403)

    except Exception as e:
        print(str(e))
        return Response(str(e), status=200)

    return Response(status=200)


@bp.route("/similarity/guid", methods=["GET", "POST"])
def get_similarity_guids():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory
    if request.method == "GET":
        return jsonify(cw.get_new_guid(cur))

    try:
        if request.json["user_id"] is not None:
            cw.add_users(cur, [request.json])
            cdb.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding user guid", status=500)

    return Response(status=200)


@bp.get("/similarity/dataset/<int:dataset>")
def get_similarity_counts(dataset):
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    try:
        return jsonify(cw.get_similar_count_by_dataset(cur, dataset))
    except Exception as e:
        print(str(e))
        return Response("error getting similarity data", status=500)


@bp.get("/similarity/target/<target>")
def get_similarity_counts_for_target(target):
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory
    try:
        limit = int(request.args.get("limit", 0))
        minUnique = int(request.args.get("minUnique", 1))
        return jsonify(cw.get_similar_items_for_target(cur, target, limit, minUnique))
    except Exception as e:
        print(str(e))
        return Response("error getting similarity data", status=500)


@bp.post("/add/similarity")
def add_similarity():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    count = 0
    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)
    ip = request.json.get('ip', None)
    cw_id = request.json.get('cwId', None)

    data = request.json["info"]
    sims = request.json["rows"]
    dsid = data["dataset_id"]

    try:
        client = cw.get_client(cur, cid, guid, ip, cw_id)
        if client is None:
            return Response("you may not", status=403)

        cw.add_submission(cur, client, data, sims)
        cdb.commit()
        count = cw.get_submissions_count_by_client_dataset(cur, client["id"], dsid)
        # log update to other database
        db_wrapper.log_update(db.cursor(), "similarity", dsid)
        db_wrapper.log_update(db.cursor(), "crowd", dsid)
        db.commit()
    except Exception as e:
        return Response(str(e), status=500)

    return jsonify({ "submissions": count })


@bp.post("/delete/similarity")
def delete_similarity():
    cur = cdb.cursor()
    cur.row_factory = db_wrapper.dict_factory

    ids = request.json["ids"]
    cid = request.json.get('client', None)
    guid = request.json.get('guid', None)

    if len(ids) == 0:
        return Response(status=200)

    try:
        client = cw.get_client(cur, cid, guid)
        if client is None:
            return Response("you may not", status=403)

        dsid = cw.get_dataset_by_similarity(cur, ids[0])
        cw.delete_similarities(cur, ids)
        cdb.commit()
        # log update to other database
        db_wrapper.log_update(db.cursor(), "similarity", dsid)
        db_wrapper.log_update(db.cursor(), "crowd", dsid)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting similarity", status=500)

    return Response(status=200)

###################################################
## Data import
###################################################

@bp.get("/import/steam/id/<steamid>")
def import_from_steam_id(steamid):
    try:
        result = get_gamedata_from_id(str(steamid))
        return jsonify({"data": [result]})
    except Exception as e:
        print(str(e))
        return Response("error getting steam data", status=500)


@bp.get("/import/steam/name/<steamname>")
def import_from_steam_name(steamname):
    try:
        result = get_gamedata_from_name(steamname)
        return jsonify({"data": result})
    except Exception as e:
        print(str(e))
        return Response("error getting steam data", status=500)


@bp.get("/import/openlibrary/isbn/<isbn>")
def import_from_openlibrary_isbn(isbn):
    result = search_openlibray_by_isbn(isbn)
    return jsonify({"data": result})


@bp.get("/import/openlibrary/title/<title>")
def import_from_openlibrary_title(title):
    result = search_openlibray_by_title(str(title))
    return jsonify({"data": result})


@bp.get("/import/openlibrary/author/<author>")
def import_from_openlibrary_author(author):
    result = search_openlibray_by_author(str(author))
    return jsonify({"data": result})

###################################################
## Clustering
###################################################

@bp.post('/clustering/<method>')
def cluster_data(method):

    if "data" not in request.json:
        return Response("missing item vectors", status=400)

    data = request.json["data"]
    n = len(data)

    if method == "hdbscan":
        clust = HDBSCAN(min_cluster_size=3, min_samples=2, metric='euclidean').fit(data)
    elif method == "dbscan":
        clust = DBSCAN(eps=50, min_samples=2, metric='euclidean').fit(data)
    elif method == "agglo":
        clust = AgglomerativeClustering(n_clusters=int(n/12), metric="euclidean", linkage="ward").fit(data)
    elif method == "meanshift":
        clust = MeanShift().fit(data)
    else:
        clust = KMeans(n_clusters=int(n/12)).fit(data)

    res = [int(i) for i in clust.labels_]

    return jsonify(res)

###################################################
## Inter-rater agreement
###################################################

@bp.get('/irr/code/<int:code>/tags')
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


@bp.get('/irr/code/<int:code>/items')
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

@bp.get('/lobby/<game_id>/code/<code_id>')
def get_rooms_for_game(game_id, code_id):
    try:
        rooms = lobby_manager.get_rooms(game_id, int(code_id))
    except Exception as e:
        print(str(e))
        return Response("error getting room", status=500)

    return jsonify(rooms)

@bp.get('/lobby/<game_id>/room/<room_id>')
def get_room(game_id, room_id):
    try:
        room = lobby_manager.get_room(game_id, room_id)
        if room is None:
            return Response("could not find room", status=500)
    except Exception as e:
        print(str(e))
        return Response("error getting room", status=500)

    return jsonify(room)

@bp.post('/lobby/<game_id>/open')
def open_room(game_id):

    if "id" not in request.json:
        return Response("missing room id", status=400)
    if "code_id" not in request.json:
        return Response("missing room id", status=400)
    if "name" not in request.json:
        return Response("missing player name", status=400)

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

@bp.post('/lobby/<game_id>/close')
def close_room(game_id):

    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=400)

    try:
        room_id = request.json["room_id"]
        lobby_manager.close(game_id, room_id)
    except Exception as e:
        print(str(e))
        return Response("error closing room", status=500)

    return Response("okay", status=200)

@bp.post('/lobby/<game_id>/update')
def update_room(game_id):
    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=400)

    room_id = request.json["room_id"]
    try:
        lobby_manager.update_room(game_id, room_id)
    except Exception as e:
        print(str(e))
        return Response("error updating room", status=500)

    return Response("okay", status=200)

@bp.post('/lobby/<game_id>/join')
def join_room(game_id):

    if "room_id" not in request.json:
        print("missing room id")
        return Response("missing room id", status=400)
    if "id" not in request.json:
        print("missing player id")
        return Response("missing player id", status=400)
    if "name" not in request.json:
        print("missing player name")
        return Response("missing player name", status=400)

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

@bp.post('/lobby/<game_id>/leave')
def leave_room(game_id):

    if "room_id" not in request.json:
        return Response("missing room id", status=400)
    if "id" not in request.json:
        return Response("missing player id", status=400)

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

@bp.get('/game_scores/code/<int:code>')
def get_game_scores(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_by_code(cur, code)
    return jsonify(res)


@bp.get('/game_scores_items/code/<int:code>')
def get_game_scores_items(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_items_by_code(cur, code)
    return jsonify(res)


@bp.get('/game_scores_tags/code/<int:code>')
def get_game_scores_tags(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    res = db_wrapper.get_game_scores_tags_by_code(cur, code)
    return jsonify(res)


@bp.post("/add/game_scores")
def add_game_scores():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores(cur, request.json["rows"])
        if cur.rowcount > 0:
            db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores", status=500)

    return Response(status=200)


@bp.post("/add/game_scores_items")
def add_game_scores_items():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores_items(cur, request.json["rows"])
        if cur.rowcount > 0:
            db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores items", status=500)

    return Response(status=200)


@bp.post("/add/game_scores_tags")
def add_game_scores_tags():
    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_game_scores_tags(cur, request.json["rows"])
        if cur.rowcount > 0:
            db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding game scores tags", status=500)

    return Response(status=200)

###################################################
## GET Data
###################################################

@bp.get("/datasets")
def get_datasets():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    try:
        datasets = db_wrapper.get_datasets(cur)
        return jsonify([dict(d) for d in datasets])
    except Exception as e:
        print(str(e))
        return Response("error loading datasets", status=500)

@bp.get("/items/dataset/<int:dataset>")
def get_items_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_items_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/items/code/<int:code>")
def get_items_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_items_by_code(cur, int(code))
    return jsonify([dict(d) for d in data])


@bp.get("/finalized/code/<int:code>")
def get_finalized_items_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    try:
        return jsonify(db_wrapper.get_items_finalized_by_code(cur, code))
    except Exception as e:
        print(str(e))
        return Response("error getting finalized items", status=500)


@bp.get("/finalized/user/<int:user_id>")
def get_finalized_items_by_user(user_id):

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory

    try:
        return jsonify(db_wrapper.get_items_finalized_by_user(cur, user_id))
    except Exception as e:
        print(str(e))
        return Response("error getting finalized items", status=500)


@bp.get("/item_expertise/dataset/<int:dataset>")
def get_item_expertise(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_item_expertise_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/users")
def get_users():
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_users(cur)
    try:
        guids = cw.get_users(cur)
        for d in data:
            g = [dg["guid"] for dg in guids if dg["user_id"] == d["id"]]
            d["guid"] = g[0] if len(g) > 0 else None
    except:
        pass

    return jsonify([dict(d) for d in data])


@bp.get("/users/dataset/<int:dataset>")
def get_users_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_users_by_dataset(cur, dataset)

    try:
        guids = cw.get_users_by_dataset(cur, dataset)
        for d in data:
            g = [dg["guid"] for dg in guids if dg["user_id"] == d["id"]]
            d["guid"] = g[0] if len(g) > 0 else None
    except:
        pass

    return jsonify([dict(d) for d in data])


@bp.get("/codes/dataset/<int:dataset>")
def get_codes_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_codes_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/tags/dataset/<int:dataset>")
def get_tags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/tags/code/<int:code>")
def get_tags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_tags_by_code(cur, code)
    return jsonify([dict(d) for d in data])


@bp.get("/datatags/dataset/<int:dataset>")
def get_datatags_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in data])


@bp.get("/datatags/code/<int:code>")
def get_datatags_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_code(cur, code)
    return jsonify([dict(d) for d in data])


@bp.get("/datatags/tag/<tag>")
def get_datatags_tag(tag):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    data = db_wrapper.get_datatags_by_tag(cur, tag)
    return jsonify([dict(d) for d in data])


@bp.get("/evidence/dataset/<int:dataset>")
def get_evidence_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in evidence])


@bp.get("/evidence/code/<int:code>")
def get_evidence_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    evidence = db_wrapper.get_evidence_by_code(cur, code)
    return jsonify([dict(d) for d in evidence])


@bp.get("/tag_assignments/dataset/<int:dataset>")
def get_tag_assignments_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_dataset(cur, dataset)
    return jsonify([dict(d) for d in tas])


@bp.get("/tag_assignments/code/<int:code>")
def get_tag_assignments(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_old_code(cur, code)
    return jsonify([dict(d) for d in tas])


@bp.get("/tag_assignments/old/<old_code>/new/<new_code>")
def get_tag_assignments_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    tas = db_wrapper.get_tag_assignments_by_codes(cur, old_code, new_code)
    return jsonify([dict(d) for d in tas])


@bp.get("/code_transitions/dataset/<int:dataset>")
def get_code_transitions(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/code_transitions/code/<int:code>")
def get_code_transitions_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_old_code(cur, code)
    return jsonify(result)


@bp.get("/code_transitions/old/<old_code>/new/<new_code>")
def get_code_transitions_by_codes(old_code, new_code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_code_transitions_by_codes(cur, old_code, new_code)
    return jsonify(result)


@bp.get("/meta_groups/dataset/<int:dataset>")
def get_meta_groups_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_groups_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/meta_groups/code/<int:code>")
def get_meta_groups_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_groups_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_items/dataset/<int:dataset>")
def get_mitems_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_items_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/meta_items/code/<int:code>")
def get_mitems_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_items_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_categories/code/<int:code>")
def get_meta_cats_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_categories_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_agreements/code/<int:code>")
def get_meta_agree_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_agreements_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_cat_connections/dataset/<int:dataset>")
def get_meta_cat_conns_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_cat_conns_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/meta_cat_connections/code/<int:code>")
def get_meta_cat_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_cat_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_tag_connections/dataset/<int:dataset>")
def get_meta_tag_conns_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_tag_conns_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/meta_tag_connections/code/<int:code>")
def get_meta_tag_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_tag_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/meta_ev_connections/dataset/<int:dataset>")
def get_meta_ev_conns_by_dataset(dataset):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_ev_conns_by_dataset(cur, dataset)
    return jsonify(result)


@bp.get("/meta_ev_connections/code/<int:code>")
def get_meta_ev_conns_by_code(code):
    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    result = db_wrapper.get_meta_ev_conns_by_code(cur, code)
    return jsonify(result)


@bp.get("/objections/code/<int:code>")
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

@bp.post("/add/datasets")
@flask_login.login_required
def add_datasets():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        ids = db_wrapper.add_datasets(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding datasets", status=500)

    return jsonify({ "ids": ids })


@bp.post("/import")
@flask_login.login_required
def upload_data():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    body = request.json

    if "dataset" not in body and "dataset_id" not in body:
        print("missing dataset")
        return Response("missing dataset", status=400)

    existing = "dataset_id" in body and body["dataset_id"] is not None

    if existing and "code_id" not in body:
        print("missing code")
        return Response("missing code", status=400)

    if "users" not in body:
        print("missing users")
        return Response("missing users", status=400)

    if "datatags" in body and "dt_user" not in body:
        print("missing user for datatags")
        return Response("missing user for user tags", status=400)

    if "items" not in body and "tags" not in body and "datatags" not in body:
        print("import: missing data")
        return Response("missing data", status=400)

    cur.row_factory = db_wrapper.namedtuple_factory

    user_id = None
    ds_id = None

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
                    return Response("missing user name", status=400)

        except ValueError as e:
            print(str(e))
            return Response("error importing data", status=500)

    else:
        dataset = body["dataset"]

        try:
            ds_id = db_wrapper.add_dataset_return_id(cur, dataset)
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

    tids = {}
    iids = {}

    try:
        now = db_wrapper.get_millis()

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

        # add items
        if "items" in body:
            items = body["items"]

            for d in items:

                d["dataset_id"] = ds_id
                d["code_id"] = code_id
                d["created"] = now
                d["created_by"] = user_id

                dspath = str(ds_id)

                if "teaser" in d and d["teaser"] is not None and len(d["teaser"]) > 0:
                    if validators.url(d["teaser"]):
                        url = d["teaser"]
                        filename = save_teaser_from_url(url, dspath)
                        if filename:
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

    return jsonify({ "id": ds_id, "item_ids": iids, "tag_ids": tids })

@bp.post("/add/users")
@flask_login.login_required
def add_users():
    user = flask_login.current_user
    if user.is_admin:
        cur = db.cursor()
        cur.row_factory = db_wrapper.namedtuple_factory
        try:
            db_wrapper.add_users(cur, request.json["rows"])
            db.commit()
            return Response(status=200)
        except Exception as e:
            print(str(e))
            return Response("error adding user", status=500)

    return Response("only allowed for admins", status=401)

@bp.post("/add/items")
@flask_login.login_required
def add_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    rows = request.json["rows"]

    for e in rows:
        # if we have no teaser already uploaded
        if e["teaser"] == None:
            name = e.get("teaserName", "")
            url = e.get("teaserUrl", "")

            dspath = str(e["dataset_id"])

            if url:
                filename = save_teaser_from_url(url, dspath)
                if filename:
                    e["teaser"] = filename
            elif name:
                suff = [p.suffix for p in TEASER_PATH.joinpath(dspath).glob(name + ".*")][0]
                if not suff:
                    print("image does not exist")
                    continue

                e["teaser"] = name + suff
    try:
        ids = db_wrapper.add_items(cur, request.json["dataset"], request.json["code"], rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding items", status=500)

    return jsonify({ "ids": ids })


@bp.post("/add/finalized")
@flask_login.login_required
def finalize_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    rows = request.json["rows"]

    try:
        db_wrapper.finalize_items(cur, rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating items", status=500)

    return Response(status=200)


@bp.post("/add/item_expertise")
@flask_login.login_required
def add_item_expertise():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_item_expertise(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding item expertise", status=500)

    return Response(status=200)


@bp.post("/add/codes")
@flask_login.login_required
def add_codes():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_codes(cur, request.json["dataset"], request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding codes", status=500)

    return Response(status=200)


@bp.post("/add/tags")
@flask_login.login_required
def add_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tags", status=500)

    return Response(status=200)


@bp.post("/add/datatags")
@flask_login.login_required
def add_datatags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_datatags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding datatags", status=500)

    return Response(status=200)


@bp.post("/add/tags/assign")
@flask_login.login_required
def add_tags_for_assignment():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.dict_factory
    try:
        db_wrapper.add_tags_for_assignment(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tags for assignment", status=500)
    return Response(status=200)


@bp.post("/add/tag_assignments")
@flask_login.login_required
def add_tag_assignments():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_tag_assignments(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding tag assignments", status=500)

    return Response(status=200)


@bp.post("/add/meta_items")
@flask_login.login_required
def add_meta_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_items(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta items", status=500)

    return Response(status=200)


@bp.post("/add/meta_agreements")
@flask_login.login_required
def add_meta_agreements():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_agreements(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta agreements", status=500)

    return Response(status=200)


@bp.post("/add/meta_categories")
@flask_login.login_required
def add_meta_categories():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

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


@bp.post("/add/objections")
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

@bp.post("/update/datasets")
@flask_login.login_required
def update_datasets():
    user = flask_login.current_user
    if user.is_admin:
        cur = db.cursor()
        cur.row_factory = db_wrapper.namedtuple_factory
        try:
            db_wrapper.update_datasets(cur, request.json["rows"])
            db.commit()
            return Response(status=200)
        except Exception as e:
            print(str(e))
            return Response("error updating datasets", status=500)

    return Response("only allowed for admins", status=401)


@bp.post("/update/users")
@flask_login.login_required
def update_users():
    user = flask_login.current_user
    if user.is_admin:
        cur = db.cursor()
        cur.row_factory = db_wrapper.namedtuple_factory
        try:
            db_wrapper.update_users(cur, request.json["rows"])
            db.commit()
            return Response(status=200)
        except Exception as e:
            print(str(e))
            return Response("error updating users", status=500)

    return Response("only allowed for admins", status=401)


@bp.post("/update/codes")
@flask_login.login_required
def update_codes():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_codes(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating codes", status=500)
    return Response(status=200)


@bp.post("/update/tags")
@flask_login.login_required
def update_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_tags(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating tags", status=500)
    return Response(status=200)


@bp.post("/update/item_expertise")
@flask_login.login_required
def update_item_expertise():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_item_expertise(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating item expertise", status=500)

    return Response(status=200)


@bp.post("/update/items")
@flask_login.login_required
def update_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    rows = request.json["rows"]
    for e in rows:
        name = e.get("teaserName", "")
        filepath = e.get("teaser", "")
        dspath = str(e["dataset_id"])

        if name:
            suff = [p.suffix for p in TEASER_PATH.joinpath(dspath).glob(name + ".*")][0]
            if not suff:
                print("image does not exist")
                continue

            if filepath:
                p = TEASER_PATH.joinpath(dspath, filepath)
                if p.exists():
                    p.unlink()

            e["teaser"] = name + "." + suff

    try:
        db_wrapper.update_items(cur, rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating items", status=500)

    return Response(status=200)


@bp.post("/update/evidence")
@flask_login.login_required
def update_evidence():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    rows = request.json["rows"]
    for e in rows:
        name = e.get("filename", "")
        dspath = str(db_wrapper.get_dataset_id_by_code(cur, e["code_id"]))
        if name:
            suff = [p.suffix for p in EVIDENCE_PATH.joinpath(dspath).glob(name + ".*")][0]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name + suff

    try:
        db_wrapper.update_evidence(cur, request.json["rows"], EVIDENCE_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating evidence", status=500)

    return Response(status=200)


@bp.post("/update/tag_assignments")
@flask_login.login_required
def update_tag_assignments():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    try:
        db_wrapper.update_tag_assignments(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating tag assignments", status=500)

    return Response(status=200)


@bp.post("/update/meta_groups")
@flask_login.login_required
def update_meta_groups():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    try:
        db_wrapper.update_meta_groups(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta groups", status=500)

    return Response(status=200)


@bp.post("/update/meta_items")
@flask_login.login_required
def update_meta_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_items(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta items", status=500)

    return Response(status=200)


@bp.post("/update/meta_agreements")
@flask_login.login_required
def update_meta_agreements():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_agreements(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta agreements", status=500)

    return Response(status=200)


@bp.post("/update/meta_categories")
@flask_login.login_required
def update_meta_categories():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_meta_categories(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating meta categories", status=500)

    return Response(status=200)


@bp.post("/update/objections")
@flask_login.login_required
def update_objections():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

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

@bp.post("/delete/datasets")
@flask_login.login_required
def delete_datasets():
    user = flask_login.current_user
    if user.is_admin:
        cur = db.cursor()
        cur.row_factory = db_wrapper.namedtuple_factory
        try:
            db_wrapper.delete_datasets(cur, request.json["ids"], TEASER_PATH, EVIDENCE_PATH)
            db.commit()
            return Response(status=200)
        except Exception as e:
            print(str(e))
            return Response("error deleting datasets", status=500)

    return Response("only allowed for admins", status=401)


@bp.post("/delete/users")
@flask_login.login_required
def delete_users():
    user = flask_login.current_user
    if user.is_admin:
        cur = db.cursor()
        cur.row_factory = db_wrapper.namedtuple_factory
        try:
            db_wrapper.delete_users(cur, request.json["ids"])
            db.commit()
            return Response(status=200)
        except:
            return Response("error deleting users", status=500)

    return Response("only allowed for admins", status=401)


@bp.post("/delete/items")
@flask_login.login_required
def delete_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_items(cur, request.json["ids"], TEASER_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting items", status=500)

    return Response(status=200)


@bp.post("/delete/tags")
@flask_login.login_required
def delete_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_tags(cur, request.json["ids"], EVIDENCE_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting tags", status=500)
    return Response(status=200)


@bp.post("/delete/item_expertise")
@flask_login.login_required
def delete_item_expertise():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_item_expertise(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting item expertise", status=500)

    return Response(status=200)


@bp.post("/delete/datatags")
@flask_login.login_required
def delete_datatags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_datatags(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting datatags", status=500)
    return Response(status=200)


@bp.post("/delete/evidence")
@flask_login.login_required
def delete_evidence():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_evidence(cur, request.json["ids"], EVIDENCE_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting evidence", status=500)

    return Response(status=200)


@bp.post("/delete/tag_assignments")
@flask_login.login_required
def delete_tag_assignments():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_tag_assignments(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting tag assignments", status=500)

    return Response(status=200)


@bp.post("/delete/code_transitions")
@flask_login.login_required
def delete_code_transitions():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_code_transitions(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting code transtion", status=500)

    return Response(status=200)


@bp.post("/delete/meta_items")
@flask_login.login_required
def delete_meta_items():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_items(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta items", status=500)

    return Response(status=200)


@bp.post("/delete/meta_cat_conns")
@flask_login.login_required
def delete_meta_cat_conns():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_cat_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta category connections", status=500)

    return Response(status=200)


@bp.post("/delete/meta_tag_conns")
@flask_login.login_required
def delete_meta_tag_conns():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_tag_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta tag connections", status=500)

    return Response(status=200)


@bp.post("/delete/meta_ev_conns")
@flask_login.login_required
def delete_meta_ev_conns():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_ev_conns(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta evidence connections", status=500)

    return Response(status=200)


@bp.post("/delete/meta_agreements")
@flask_login.login_required
def delete_meta_agreements():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_agreements(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta agreements", status=500)

    return Response(status=200)


@bp.post("/delete/meta_categories")
@flask_login.login_required
def delete_meta_categories():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.delete_meta_categories(cur, request.json["ids"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error deleting meta categories", status=500)

    return Response(status=200)


@bp.post("/delete/objections")
@flask_login.login_required
def delete_objections():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

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

@bp.post("/image/evidence/<int:dataset>/<name>")
@flask_login.login_required
def upload_image_evidence(dataset, name):

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    if "file" not in request.files:
        return Response("missing evidence image", status=400)

    filename = ""
    try:
        dspath = str(dataset)
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = save_evidence(file, name, dspath)
    except Exception as e:
        print(str(e))
        return Response("error uploading evidence image", status=500)

    return jsonify({ "name": filename })


@bp.post("/image/teaser/<int:dataset>/<name>")
@flask_login.login_required
def upload_image_teaser(dataset, name):

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    if "file" not in request.files:
        return Response("missing teaser image", status=400)

    final = ""
    try:
        dspath = str(dataset)
        file = request.files["file"]
        if file and allowed_file(file.filename):
            final = save_teaser(file, name, dspath)
    except Exception as e:
        print(str(e))
        return Response("error uploading teaser image", status=500)

    return jsonify({ "name": final })

@bp.post("/image/teasers/<int:dataset>")
@flask_login.login_required
def upload_image_teasers(dataset):

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    dspath = str(dataset)
    final = []
    for name, file in request.files.items():
        try:
            if file and allowed_file(file.filename):
                final.append(save_teaser(file, name, dspath))
        except Exception as e:
            print(str(e))
            return Response("error uploading teaser image", status=500)

    return jsonify({ "names": final })

@bp.post("/group/tags")
@flask_login.login_required
def group_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.group_tags(cur, request.json["parent"], request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error grouping tags", status=500)

    return Response(status=200)


@bp.post("/split/tags")
@flask_login.login_required
def split_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.split_tags(cur, request.json["rows"], EVIDENCE_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error splitting tags", status=500)

    return Response(status=200)


@bp.post("/merge/tags")
@flask_login.login_required
def merge_tags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.merge_tags(cur, request.json["rows"], EVIDENCE_PATH)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error mergin tags", status=500)

    return Response(status=200)


@bp.post("/add/evidence")
@flask_login.login_required
def add_evidence():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    rows = request.json["rows"]
    for e in rows:

        if "filename" in e:
            name = e["filename"]
            e["filepath"] = None

            dspath = str(db_wrapper.get_dataset_id_by_code(cur, e["code_id"]))

            suff = [p.suffix for p in EVIDENCE_PATH.joinpath(dspath).glob(name + ".*")]
            if not suff:
                print("image does not exist")
                continue

            e["filepath"] = name + suff[0]

    try:
        db_wrapper.add_evidence(cur, rows)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding evidence", status=500)

    return Response(status=200)


@bp.post("/add/meta_cat_conns")
@flask_login.login_required
def add_meta_cat_conns():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.add_meta_cat_conns(cur, request.json["rows"])
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error adding meta category connections", status=500)

    return Response(status=200)


@bp.post("/update/item/datatags")
@flask_login.login_required
def update_item_datatags():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory
    try:
        db_wrapper.update_item_datatags(cur, request.json)
        db.commit()
    except Exception as e:
        print(str(e))
        return Response("error updating item datatags", status=500)

    return Response(status=200)


@bp.post("/start/code_transition")
@flask_login.login_required
def start_code_transition():

    user = flask_login.current_user
    if not user.can_edit:
        return Response("data editing not allowed for guests", status=401)

    cur = db.cursor()
    cur.row_factory = db_wrapper.namedtuple_factory

    oldcode = request.json["old_code"]
    new_code_data = request.json["new_code"]

    has_old = cur.execute("SELECT * FROM codes WHERE id = ?;", (oldcode,)).fetchone()
    if not has_old:
        return Response("missing old code", status=400)

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
