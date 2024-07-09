import argparse
import sys
import os

sys.path.insert(0, os.path.abspath('BlackWhite'))
sys.path.insert(0, os.path.abspath('ORAS'))
sys.path.insert(0, os.path.abspath('Platinum'))

import BlackWhite.getShowdownData as BW
import ORAS.getShowdownData as ORS
import Platinum.getShowdownData as Pt

class ShowdownWrapper():
    def __init__(self) -> None:
        self.gameVersions = {
            "Pt": Pt.PlatinumShowdown,
            "BW": BW.getShowdownData,
            "ORAS": ORS.ORAShowdown
        }

        self.parser = self.initParser()
        self.args = self.parser.parse_args()

        self.gameVersions[self.args.gameVersion]()

    def initParser(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("gameVersion", choices = self.gameVersions.keys(), help = "the game you are playing")

        return parser

if __name__ == "__main__":
    ShowdownWrapper()