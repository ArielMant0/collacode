import re
import requests
from typing import List


def get_gamedata_from_names(names: List[str]):
    games = []

    # TODO this is not that smart, since the applist is requested for every game
    for name in names:
        games.append(get_gamedata_from_name(name))

    return games

def get_gamedata_from_name(name: str, limit: int = 10, test_limit:int = 20):
    response = _steam_request(f"https://api.steampowered.com/ISteamApps/GetAppList/v2/")
    applist_json = response.json()

    candidates = []
    ids = {}
    name = name.lower().replace(" ", "")

    for app in applist_json["applist"]["apps"]:
        lower = app["name"].lower().replace(" ", "")
        id = str(app["appid"])
        if id in ids:
            continue

        if lower == name:
            candidates.append((id, app["name"], 0))
            ids[id] = True
        elif lower.startswith(name) or lower.endswith(name):
            candidates.append((id, app["name"], 1 + min(10, abs(len(lower)-len(name)))))
            ids[id] = True
        elif re.match(name, app["name"], re.IGNORECASE):
            candidates.append((id, app["name"], 11 + abs(len(lower)-len(name))))
            ids[id] = True

    candidates = sorted(candidates, key=lambda a: a[2])

    idx = 0
    result = []

    while len(result) < limit and idx < len(candidates) and idx < test_limit:
        app = candidates[idx][0]
        data = get_gamedata_from_id(app)
        if data["type"] == "game":
            result.append(data)

        idx += 1

    return result

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
    game["tags"] = _load_game_tags(id)
    game["img"] = _load_game_image(id)
    return game

def _reduce_game_name(name: str):
    return re.sub(
        r"[ *|()/.,-_]",
        r"",
        name
    )

def _get_game_url(id):
    return f"https://store.steampowered.com/app/{id}"

def _load_game_image(id: str):
    # TODO header.jpg might not always work
    # header.jpg should always work, there are regional special versions,
    # but the generalized URL should also work in such cases
    return f"https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg"
    response = _steam_request(
        f"https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg"
    )
    return response.raw

def _load_game_tags(id: str):
    response = _steam_request(f"https://steamspy.com/api.php?request=appdetails&appid={id}")
    details_json = response.json()
    return details_json["tags"]

def _load_game_metadata(id: str):
    response = _steam_request(f"https://store.steampowered.com/api/appdetails?appids={id}")
    details_json = response.json()

    release_date = None
    name = None
    item_type = None

    if "data" in details_json[id]:
        item_type = details_json[id]["data"]["type"]
        release_date = details_json[id]["data"]["release_date"]["date"]

        if "name" in details_json[id]["data"]:
            name = details_json[id]["data"]["name"]
        else:
            print(f"No name found for game: {id}")
    else:
        print(f"No release_date found for game: {id}")

    return (
        name,
        release_date,
        item_type
    )

def _steam_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        raise SystemExit(errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        raise SystemExit(err)

    return response
