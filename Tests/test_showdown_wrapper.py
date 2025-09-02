import argparse
import unittest
import sys

sys.path.append(r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator")
import showdown

class showdownTestPt(unittest.TestCase):
    def setUp(self):
        print("\nTesting Pt")
        mode = "unittest"
        test_param = {
            "game_version": "Pt"
        }

        self.showdown = showdown.ShowdownWrapper(mode, test_param)

    def test_showdown(self):
        self.showdown

    def tearDown(self):
        return super().tearDown()

class showdownTestBW(unittest.TestCase):
    def setUp(self):
        print("\nTesting BW")
        mode = "unittest"
        test_param = {
            "game_version": "BW"
        }

        self.showdown = showdown.ShowdownWrapper(mode, test_param)

    def test_showdown(self):
        self.showdown

    def tearDown(self):
        return super().tearDown()

class showdownTestXY(unittest.TestCase):
    def setUp(self):
        print("\nTesting XY")
        mode = "unittest"
        test_param = {
            "game_version": "XY"
        }

        self.showdown = showdown.ShowdownWrapper(mode, test_param)

    def test_showdown(self):
        self.showdown

    def tearDown(self):
        return super().tearDown()

class showdownTestORAS(unittest.TestCase):
    def setUp(self):
        print("\nTesting ORAS")
        mode = "unittest"
        test_param = {
            "game_version": "ORAS"
        }

        self.showdown = showdown.ShowdownWrapper(mode, test_param)

    def test_showdown(self):
        self.showdown

    def tearDown(self):
        return super().tearDown()
    
if __name__ == "__main__":
    unittest.main()