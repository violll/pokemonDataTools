import argparse
import sys
import os

sys.path.insert(0, os.path.abspath('BlackWhite'))
sys.path.insert(0, os.path.abspath('ORAS'))
sys.path.insert(0, os.path.abspath('Platinum'))
sys.path.insert(0, os.path.abspath('XY'))

import BlackWhite.getShowdownData as BW
import ORAS.getShowdownData as ORS
import Platinum.getShowdownData as Pt
import XY.getShowdownData as XY

GAMEVERSIONS = {
    "Pt": Pt.PlatinumShowdown,
    "BW": BW.getShowdownData,
    "ORAS": ORS.ORAShowdown,
    "XY": XY.XYShowdown
}

def getGameVersion(gameVersion):
    return gameVersion
class ShowdownWrapper():
    def __init__(self, mode = "normal", test_param = None) -> None:
        # validate argument options
        self.parse_args(mode, test_param)
        
        # access showdown data
        GAMEVERSIONS[self.game_version]()

    def parse_args(self, mode, test_param):
        if mode == "unittest":
            if test_param is None:
                raise ValueError("please provide arguments for testing")

            self.game_version = test_param["game_version"]
        
        else:
            parser = argparse.ArgumentParser()
            parser.add_argument("-v",                              \
                                "--game_version",                  \
                                choices = GAMEVERSIONS.keys(),     \
                                help = "the game you are playing", \
                                required=True)
            
            args = parser.parse_args()

            self.game_version = args.game_version

    def get_game_version(self):
        return self.game_version

if __name__ == "__main__":
    ShowdownWrapper()