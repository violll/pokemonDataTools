from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import pandas as pd
import sys
import os
import io
import json

sys.path.insert(0, os.path.abspath('ShowdownGenerator'))
import showdownPokemon, showdownTrainer

class ORAShowdown:
    def __init__(self) -> None:
        self.txt = self.readTrainerData()
        self.formatTrainer()

    def readTrainerData(self):
        f = open("ShowdownGenerator/ORAS/ORASTrainers.txt", "r", encoding = 'utf-8')
        return f.read().split("\n\n")

    def formatTrainer(self):
        possibleTrainers = []

        while possibleTrainers == []:
            desiredTrainer = input("What is the trainer name?\n> ")
            
            # search for multiple versions of the same trainer
            for i in range(len(self.txt)):
                if desiredTrainer in self.txt[i]: possibleTrainers.append(i)

            if possibleTrainers == []: print("Please type a valid trainer name!")

        # user selects the appropriate trainer
        if len(possibleTrainers) > 1: 
            for i in possibleTrainers: print(self.txt[i] + "\n")
            trainerI = int(input("Which version is correct?\n> ")) - 1
            trainer = self.txt[int(trainerI)].split("\n")[1:]
        else: 
            trainer = self.txt[possibleTrainers[0]].split("\n")[1:]
            trainerI = trainer[0].split("-")[0]
        
        # updates trainer name to verify search accuracy
        desiredTrainer = trainer[0].split("- ")[-1]
        pokemonList = trainer[3:]
        Trainer = showdownTrainer.Trainer(desiredTrainer)

        # checks if trainer has items and writes showdown import for each pokemon
        pokemonI = 0
        for line in pokemonList:
            Trainer.pokemon.append(self.formatPokemon(line, desiredTrainer, trainerI, pokemonI))
            pokemonI += 1
        
        for mon in Trainer.pokemon: print(mon)
        return None
    
    def parseMon(self, pokemon, keyword, end=""):
        start = pokemon.find(keyword) + len(keyword)

        stop = -1
        i = 0
        while stop < start:
            if i >= len(end): break

            stop = len(pokemon[:start]) + pokemon[start:].find(end[i])
            i += 1
        if stop == -1: stop = len(pokemon)

        return pokemon[start:stop]
            
    def formatPokemon(self, pokemon, trainer, trainerI, pokemonI):
        ResTest = showdownPokemon.Pokemon()
        
        ResTest.name = pokemon.split()[0]
        # ResTest.gender TODO -- missing from doc

        # item
        if "@" in pokemon: 
            ResTest.item = "@ " + self.parseMon(pokemon, "@", ["(", "@", "IVs"]) 

        # ivs
        ResTest.IVs = ["{} {}".format(int(self.parseMon(pokemon, "IVs: All ")), stat) for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]]
        
        # ability -- if it's missing, can't assume the pokemon has only one ability...
        if "Ability" in pokemon:
            ResTest.ability = self.parseMon(pokemon, "Ability: ", [")"])
        
        # level
        ResTest.level = int(self.parseMon(pokemon, "Lv. ", ")"))
        
        # TODO nature -- missing from doc

        # moves
        if "Moves" in pokemon:
            ResTest.moves = [move for move in self.parseMon(pokemon, "Moves: ", ")").split(" / ")]
        else:
            ResTest.moves = self.getMoves(ResTest)
        
        ResTest.trainer = trainer


        return ResTest


        # # TODO check this
        # gender = self.getGender(trainer, name, trainerI, pokemonI)

    
    def getGender(self, trainer, pokemon, trainerI, pokemonI):
        genderRatio = self.getGenderRatio(pokemon)

        if len(genderRatio) == 1: return ""
        elif genderRatio[0] == 1: return "(M)"
        elif genderRatio[1] == 1: return "(F)"
        else:
            detailedTDocs = json.load(open("ShowdownGenerator/Platinum/platinumTrainers.json"))
            detailedTrainer = [t["pokemon"][pokemonI]["personality"] for t in detailedTDocs["trainers"] if t["trainer_name"] == trainer and t["rom_id"] == int(trainerI)][0]

            pGender = detailedTrainer % 256

            threshold = genderRatio[1] * 256 - 1

            if pGender >= threshold: return "(M)"
            else: return "(F)"

    
    def getGenderRatio(self, pName):
        try: 
            f = open("ShowdownGenerator/Platinum/PokemonData/genderRatios.json")
            genderData = json.load(f)
        except:
            # must make the file
            genderData = {}

        if pName in genderData.keys():
            ratios = genderData[pName]
        else:
            # get the gender ratio from bulbapedia
            req = Request("https://bulbapedia.bulbagarden.net/wiki/{}_(Pok%C3%A9mon)".format(pName))
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0")
            html = urlopen(req).read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            # navigate the soup to get the gender ratio
            genderRatio = soup.find(string="Gender ratio")  \
                        .parent                             \
                        .parent                             \
                        .parent                             \
                        .parent                             \
                        .find("table")                      \
                        .find("a")                          \
                        .text
            
            # check if genderless
            if "unknown" in genderRatio: 
                ratios = [None]
            elif "," not in genderRatio:
                # check if 100% M or F
                if "female" in genderRatio: ratios = [0, 1]
                else: ratios = [1, 0]
            else:
                # ratio is always [male%, female%]
                ratios = [float(i[:-1])/100 for i in genderRatio.replace(" female", "").replace(" male", "").split(", ")]

            # update the JSON
            genderData[pName] = ratios

            # save update
            with open("ShowdownGenerator/Platinum/PokemonData/genderRatios.json", "w") as f:
                json.dump(genderData, f)

        return ratios

    def getMoves(self, mon):
        name = mon.name
        level = mon.level

        try:
            df = pd.read_pickle("ShowdownGenerator/ORAS/PokemonData/{}.pkl".format(name))
            col = list(df)[0]
        except:
            req = Request("https://bulbapedia.bulbagarden.net/wiki/{}_(Pok%C3%A9mon)/Generation_VI_learnset".format(name))
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0")
            html = urlopen(req).read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            table = soup.find("table", {"class": "sortable"})

            try: 
                df = pd.read_html(io.StringIO(str(table)), displayed_only=False)[0].loc[:, ["ORAS", "Move"]]
                col = "ORAS"
            except:
                df = pd.read_html(io.StringIO(str(table)), displayed_only=False)[0].loc[:, ["Level", "Move"]]
                col = "Level"

            for i in range(df.shape[0]):
                val = df.loc[i, col]
                if val == "N/AN/A": 
                    df.loc[i, col] = -1
                else: df.loc[i, col] = int(str(val)[:len(str(val))//2])

            df = df[df.loc[:,col] != -1]
            df.to_pickle("ShowdownGenerator/ORAS/PokemonData/{}.pkl".format(name))

        moves = list(df[df.loc[:,col] <= int(level)].loc[:, "Move"].tail(4))        
        return moves

if __name__ == "__main__":
    ORAShowdown()