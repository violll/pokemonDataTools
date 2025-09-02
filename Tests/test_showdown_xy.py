import os
import sys
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

sys.path.insert(0, r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator\XY")
import getShowdownData

def make_test_case(x):
    class MyTestCase(unittest.TestCase):
        def setUp(self):     
            self.showdown = getShowdownData.XYShowdown(mode = "unittest")
        
        @patch("getShowdownData.get_trainer_input", return_value = x["trainer_name"], autospec=True)
        @patch("getShowdownData.get_trainer_n_input", return_value = x["trainer_num"], autospec=True)
        def test_parseTrainerName(self, mock_trainer_n, mock_trainer_name):
            self.assertEqual(self.showdown.parseTrainer(), x["pokemonList"])

        @patch("getShowdownData.get_trainer_input", return_value = x["trainer_num"], autospec=True)
        @patch("getShowdownData.get_trainer_n_input", return_value = x["trainer_num"], autospec=True)
        def test_parseTrainerNum(self, mock_trainer_n, mock_trainer_name):
            self.assertEqual(self.showdown.parseTrainer(), x["pokemonList"])

    return MyTestCase

inputs_to_test = {
    0: {
        "trainer_num": "6",
        "trainer_name": "Viola",
        "pokemonList": ["Surskit (Lv. 10)  (Moves: Quick Attack / Bubble / Water Sport) IVs: All 18",
                        "Vivillon (Lv. 12)  (Moves: Harden / Infestation / Tackle) IVs: All 18"
                        ]
    },
    1: {
        "trainer_num": "1",
        "trainer_name": "Youngster Aidan",
        "pokemonList": ["Yanma (Lv. 27)  IVs: All 0",
                        "Whirlipede (Lv. 27)  IVs: All 0",
                        "Mothim (Lv. 27)  IVs: All 0"
                        ]
    }
}

class ViolaTest(make_test_case(inputs_to_test[0])): 
    pass

class YoungsterAidanTest(make_test_case(inputs_to_test[1])):
    pass

if __name__ == "__main__":
    unittest.main()