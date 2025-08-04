import json
import os
import re
from pathlib import Path
from typing import List

import requests

CACHE_PATH = Path(os.path.dirname(os.path.abspath(__file__))).joinpath(
    "..", "data", "steam_api_cache.json"
)


def get_gamedata_from_names(names: List[str]):
    games = []

    # TODO this is not that smart, since the applist is requested for every game
    for name in names:
        games.append(get_gamedata_from_name(name))

    return games


def _parse_candidates_by_name(applist: dict, name: str, limit: int = 10, test_limit: int = 20):
    candidates = []
    ids = set()
    name = name.lower().replace(" ", "")

    if applist is None or "applist" not in applist or "apps" not in applist["applist"]:
        return []

    for app in applist["applist"]["apps"]:
        lower = app["name"].lower().replace(" ", "").split(":")
        id = app["appid"]
        if id in ids:
            continue

        if any([n == name for n in lower]):
            candidates.append((id, app["name"], 0))
            ids.add(id)
        elif any([n.startswith(name) or n.endswith(name) for n in lower]):
            candidates.append((id, app["name"], 1 + min(10, abs(len(lower) - len(name)))))
            ids.add(id)
        elif re.match(name, app["name"], re.IGNORECASE):
            candidates.append((id, app["name"], 11 + abs(len(lower) - len(name))))
            ids.add(id)

    candidates = sorted(candidates, key=lambda a: a[2])

    idx = 0
    test_num = 0
    result: List[dict] = []

    while len(result) < limit and idx < len(candidates) and test_num < test_limit:
        app = candidates[idx][0]
        data = get_gamedata_from_id(str(app))
        if data["type"] == "game":
            test_num += 1
            result.append(data)

        idx += 1

    return result


def _get_gamedata_from_cache_by_name(name: str, limit: int = 10, test_limit: int = 20):
    applist_json = {}

    try:
        with open(CACHE_PATH, "r") as file:
            applist_json = json.load(file)
            return _parse_candidates_by_name(applist_json, name, limit, test_limit)
    except:
        return []


def get_gamedata_from_name(name: str, limit: int = 10, test_limit: int = 20):

    in_cache = _get_gamedata_from_cache_by_name(name, limit, test_limit)
    if len(in_cache) > 0:
        return in_cache

    try:
        response = _steam_request("https://api.steampowered.com/ISteamApps/GetAppList/v2/")
        applist_json = response.json()

        with open(CACHE_PATH, "w") as file:
            json.dump(applist_json, file, indent=None, separators=(",", ":"))

        return _parse_candidates_by_name(applist_json, name, limit, test_limit)
    except:
        return []


def get_gamedata_from_ids(ids: List[str]):
    games = []

    for id in ids:
        data = get_gamedata_from_id(id)
        if data["type"] == "game":
            games.append(data)

    return games


def get_gamedata_from_id(id: str):
    game = {}
    game["id"] = id
    game["url"] = _get_game_url(id)
    game["name"], game["release_date"], game["type"] = _load_game_metadata(id)
    # game["tags"] = _load_game_tags(id)
    game["img"] = _load_game_image(id)
    return game


def _get_game_url(id):
    return f"https://store.steampowered.com/app/{id}"


def _load_game_image(id: str):
    # TODO header.jpg might not always work
    # header.jpg should always work, there are regional special versions,
    # but the generalized URL should also work in such cases
    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg"


def _load_game_tags(id: str):
    response = _steam_request(f"https://steamspy.com/api.php?request=appdetails&appid={id}")
    details_json = response.json()
    return details_json["tags"]


def _load_game_metadata(id: str):
    response = _steam_request(f"https://store.steampowered.com/api/appdetails?appids={id}")
    details_json = response.json()

    if id not in details_json or "data" not in details_json[id]:
        print(f"no data found for game: {id}")
        return (None, None, None)

    data = details_json[id]["data"]
    release_date = None
    name = None
    item_type = None

    name = data["name"]
    item_type = data["type"]
    release_date = data["release_date"]["date"]

    return (name, release_date, item_type)


def _steam_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return response
