import requests
from typing import List
import re
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

class Loader:
    def __init__(self):
        pass

    def get_gamedata_from_names(self, names: List[str]):
        games = []

        # TODO this is not that smart, since the applist is requested for every game
        for name in names:
            games.append(self.get_gamedata_from_name(name))

        return games

    def get_gamedata_from_name(self, name: str):
        response = self._steam_request(f"https://api.steampowered.com/ISteamApps/GetAppList/v0002/")
        applist_json = response.json()

        candidates = []

        for app in applist_json["applist"]["apps"]:
            if name in app["name"]:
                candidates.append(str(app["appid"]))

        result = []
        for app in candidates:
            result.append(self.get_gamedata_from_id(app))

        return result

    def get_gamedata_from_ids(self, ids: List[str]):
        games = []

        for id in ids:
            games.append(self.get_data_of_game(id))

        return games

    def get_gamedata_from_id(self, id: str):
        game = {}
        game["id"] = id
        game["url"] = self._get_game_url(id)
        game["name"], game["release_date"] = self._load_game_metadata(id)
        game["tags"] = self._load_game_tags(id)
        game["img"] = self._load_game_image(id)
        return game

    def _reduce_game_name(self, name: str):
        return re.sub(
            r"[ *|()/.,-_]",
            r"",
            name
        )

    def _get_game_url(self, id):
        return f"https://store.steampowered.com/app/{id}"

    def _load_game_image(self, id: str):
        # TODO header.jpg might not always work
        # header.jpg should always work, there are regional special versions,
        # but the generalized URL should also work in such cases
        response = self._steam_request(
            f"https://cdn.cloudflare.steamstatic.com/steam/apps/{id}/header.jpg"
        )
        return response.raw

    def _load_game_tags(self, id: str):
        response = self._steam_request(f"https://steamspy.com/api.php?request=appdetails&appid={id}")
        details_json = response.json()
        return details_json["tags"]

    def _load_game_metadata(self, id: str):
        response = self._steam_request(f"https://store.steampowered.com/api/appdetails?appids={id}")
        details_json = response.json()

        release_date = None
        name = None

        if "data" in details_json[id]:
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
        )

    def _steam_request(self, url):
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
