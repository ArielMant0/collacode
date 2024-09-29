import warnings
warnings.filterwarnings("ignore")

from backend.app.steam_api_loader import Loader

class MainApp:
    def __init__(self):
        l = Loader()

        # print(l.get_gamedata_from_id("65540"))
        # print(l.get_gamedata_from_ids(["65540"]))

        print(l.get_gamedata_from_name("Gothic 1"))
        # print(l.get_gamedata_from_name(["Gothic 1"]))

###################################################################################################
# Main
###################################################################################################
if __name__ == "__main__":
    main_app = MainApp()
