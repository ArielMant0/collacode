from datetime import datetime, timezone
from uuid import uuid4

def utc_now():
    return int(datetime.now(timezone.utc).timestamp() * 1000)

class Lobby:

    def __init__(self, id, user_id, name, data, game_id, code_id):
        self.id = id
        self.peer = user_id
        self.name = name
        self.data = data
        self.game_id = game_id
        self.code_id = code_id
        self.players = {}
        self.join(user_id, name)


    def get_players(self):
        aslist = []
        for id, name in self.players.items():
            aslist.append({ "id": id, "name": name })

        return aslist


    def is_empty(self):
        return len(self.players) == 0


    def describe(self):
        return {
            "id": self.id,
            "peer": self.peer,
            "name": self.name,
            "code_id": self.code_id,
            "players": self.get_players(),
            "last_update": self.last_update,
            "data": self.data
        }


    def update(self):
        self.last_update = utc_now()


    def join(self, id, name):
        if id not in self.players:
            self.players[id] = name
            self.update()
            return True

        return False


    def leave(self, id):
        if id in self.players:
            del self.players[id]
            self.update()
            return True

        return False


    def same(self, id):
        return str(self.id) == str(id)


    def __str__(self):
        return f"{self.id} ({self.peer})"


class LobbyManager:

    def __init__(self):
        self.rooms = {}
        self.last_update = {}


    def update(self, game_id):
        self.last_update[game_id] = utc_now()


    def room_exists(self, game_id, room_id):
        return self.get(game_id, room_id) is not None


    def get(self, game_id, room_id):
        if game_id not in self.rooms:
            return None

        lobbies = self.rooms[game_id]
        for lobby in lobbies:
            if lobby.same(room_id):
                return lobby

        return None


    def get_room(self, game_id, room_id):
        self.prune_rooms(game_id)
        room = self.get(game_id, room_id)
        if room is not None:
            return room.describe()

        return None


    def update_room(self, game_id, room_id):
        room = self.get(game_id, room_id)
        if room is not None:
            room.update()


    def prune_rooms(self, game_id=None):
        now = datetime.now(timezone.utc)
        max_dur = 5 * 60.0

        if game_id is None:
            for gid, room_list in self.rooms.items():
                ids = set()
                for room in room_list:
                    if len(room.players) == 0:
                        ids.add(room.id)
                    else:
                        then = datetime.fromtimestamp(room.last_update / 1000.0, timezone.utc)
                        print((now - then).total_seconds(), max_dur)
                        if (now - then).total_seconds() >= max_dur:
                            ids.add(room.id)

                for id in ids:
                    self.close(gid, id)

        elif game_id in self.rooms:
            ids = set()
            for room in self.rooms[game_id]:
                if len(room.players) == 0:
                    ids.add(room.id)
                else:
                    then = datetime.fromtimestamp(room.last_update / 1000.0, timezone.utc)
                    print((now - then).total_seconds(), max_dur)
                    if (now - then).total_seconds() >= max_dur:
                        ids.add(room.id)

            for id in ids:
                self.close(game_id, id)


    def get_rooms(self, game_id=None, code_id=None):
        self.prune_rooms(game_id)
        rooms = []
        if game_id is None:
            for room_list in self.rooms.values():
                for room in room_list:
                    if code_id is None or room.code_id == code_id:
                        rooms.append(room.describe())
        else:
            if game_id in self.rooms:
                for room in self.rooms[game_id]:
                    print(room.describe())
                    if code_id is None or room.code_id == code_id:
                        rooms.append(room.describe())

        rooms.sort(key=lambda a: a["last_update"], reverse=True)

        return rooms


    def get_players_in_room(self, game_id, room_id):
        lobby = self.get(game_id, room_id)
        if lobby is not None:
            return lobby.get_players()
        return None


    def open(self, game_id, code_id, user_id, user_name, data=None):
        if game_id not in self.rooms:
            self.rooms[game_id] = []

        room_id = uuid4()
        while self.room_exists(game_id, room_id):
            room_id = uuid4()

        self.close_with_host_and_code(game_id, user_id, code_id)

        lobby = Lobby(room_id, user_id, user_name, data, game_id, code_id)
        self.rooms[game_id].append(lobby)
        self.update(game_id)
        return lobby.describe()


    def close(self, game_id, room_id):
        if game_id not in self.rooms:
            return

        game = self.rooms[game_id]
        idx = -1
        for i, lobby in enumerate(game):
            if lobby.same(room_id):
                idx = i

        if idx >= 0:
            game.pop(idx)
            self.rooms[game_id] = game
            self.update(game_id)


    def close_with_host_and_code(self, game_id, host_id, code_id):
        if game_id not in self.rooms:
            return None

        game = self.rooms[game_id]
        idx = -1
        for i, lobby in enumerate(game):
            if lobby.peer == host_id and lobby.code_id == code_id:
                idx = i

        if idx >= 0:
            game.pop(idx)
            self.update(game_id)


    def join(self, game_id, room_id, id, name):
        lobby = self.get(game_id, room_id)
        if lobby is not None:
            lobby.join(id, name)
            self.update(game_id)
            return lobby.describe()

        return None


    def leave(self, game_id, room_id, id):
        lobby = self.get(game_id, room_id)
        if lobby is not None:
            lobby.leave(id)
            if lobby.is_empty():
                self.close(game_id, room_id)
            else:
                self.update(game_id)

