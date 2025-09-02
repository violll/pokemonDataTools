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

        @patch("getShowdownData.get_trainer_input", return_value = x["trainer_name"], autospec=True)
        @patch("getShowdownData.get_trainer_n_input", return_value = x["trainer_num"], autospec=True)
        def test_parsePokemonData(self, mock_trainer_n, mock_trainer_name):
            self.showdown.main()
            
            self.assertEqual([mon.name for mon in self.showdown.trainer.pokemon], x["pokemonNames"])
            self.assertEqual([mon.item for mon in self.showdown.trainer.pokemon], x["pokemonItems"])
            self.assertEqual([mon.ivs for mon in self.showdown.trainer.pokemon], x["pokemonIVs"])
            self.assertEqual([mon.ability for mon in self.showdown.trainer.pokemon], x["pokemonAbilities"])
            self.assertEqual([mon.level for mon in self.showdown.trainer.pokemon], x["pokemonLvls"])


    return MyTestCase

inputs_to_test = {
    0: {
        "trainer_num": "6",
        "trainer_name": "Viola",
        "pokemonList": ["Surskit (Lv. 10)  (Moves: Quick Attack / Bubble / Water Sport) IVs: All 18",
                        "Vivillon (Lv. 12)  (Moves: Harden / Infestation / Tackle) IVs: All 18"],
        "pokemonNames": ["Surskit", "Vivillon"],
        "pokemonItems": ["" for _ in range(2)],
        "pokemonIVs": [[f"18 {stat}" for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]] for _ in range(2)],
        "pokemonAbilities": ["" for _ in range(2)],
        "pokemonLvls": ["10", "12"]
    },
    1: {
        "trainer_num": "1",
        "trainer_name": "Youngster Aidan",
        "pokemonList": ["Yanma (Lv. 27)  IVs: All 0",
                        "Whirlipede (Lv. 27)  IVs: All 0",
                        "Mothim (Lv. 27)  IVs: All 0"],
        "pokemonNames": ["Yanma", "Whirlipede", "Mothim"],
        "pokemonItems": ["" for _ in range(3)],
        "pokemonIVs": [[f"0 {stat}" for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]] for _ in range(3)],
        "pokemonAbilities": ["" for _ in range(3)],
        "pokemonLvls": ["27" for _ in range(3)]
    },
    2: {
        "trainer_num": "188",
        "trainer_name": "Successor Korrina",
        "pokemonList": ["Lucario (Lv. 32) @Lucarionite (Ability: Steadfast) (Moves: Power-Up Punch) IVs: All 22"],
        "pokemonNames": ["Lucario"],
        "pokemonItems": ["@ Lucarionite"],
        "pokemonIVs": [[f"22 {stat}" for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]]],
        "pokemonAbilities": ["Steadfast"],
        "pokemonLvls": ["32"]
    }
}

class ViolaTest(make_test_case(inputs_to_test[0])): 
    pass

class YoungsterAidanTest(make_test_case(inputs_to_test[1])):
    pass

class SuccessorKorrinaTest(make_test_case(inputs_to_test[2])):
    pass

if __name__ == "__main__":
    unittest.main()