from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import pandas as pd
import io
import json

class PlatinumShowdown:
    def __init__(self) -> None:
        self.txt = self.readTrainerData()
        self.formatTrainer()

    def readTrainerData(self):
        f = open("ShowdownGenerator/Platinum/Full Pokemon Platinum Trainer Data.txt", "r")
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
            for i in possibleTrainers: print(self.txt[i])
            trainerI = int(input("Which version is correct?\n> "))
            trainer = self.txt[int(trainerI)].split("\n")[1:]
        else: 
            trainer = self.txt[possibleTrainers[0]].split("\n")[1:]
            trainerI = trainer[0].split(":")[0]
        
        # updates trainer name to verify search accuracy
        desiredTrainer = trainer[0].split(": ")[-1]

        # checks if trainer has items and writes showdown import for each pokemon
        res = ""
        isMon = False
        pokemonI = 0
        for line in trainer:
            if "Item" in line: print("WARNING: {} has {}".format(desiredTrainer, line.replace("Items", "items")))
            if isMon: 
                res += self.formatPokemon(line, desiredTrainer, trainerI, pokemonI)
                pokemonI += 1
            if "=" in line: isMon = True
        
        print(res)
        return res
            
    def formatPokemon(self, pokemon, trainer, trainerI, pokemonI):
        res = ""
        attributes = pokemon.split(" ")
        name = attributes[0]
        level = attributes[2]
        gender = self.getGender(trainer, name, trainerI, pokemonI)

        attributeDict = dict()
        attributeStr = pokemon[pokemon.find("(")+1:-1].split(",")
        for attr in attributeStr:
            key, val = attr.split(": ")
            attributeDict[key.strip()] = val.strip()

        # if IVs are different for each stat
        if "/" in attributeDict["IVs"]:
            attributeDict["IVs"] = attributeDict["IVs"].split("/")
            print(attributeDict["IVs"])
        else:
            attributeDict["IVs"] = [attributeDict["IVs"] for _ in range(6)]

        res += "{} ({}) {}\n".format(trainer, name, gender)
        res += "IVs: {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe\n".format(attributeDict["IVs"][0], attributeDict["IVs"][1], attributeDict["IVs"][2], attributeDict["IVs"][3], attributeDict["IVs"][4], attributeDict["IVs"][5])
        res += "Ability: {}\n".format(attributeDict["Ability"])
        res += "Level: {}\n".format(level)
        res += "{} Nature\n".format(attributeDict["Nature"])
        if attributeDict["Moves"] == "Default":
            res += self.getMoves(name, level)
        else: 
            for move in attributeDict["Moves"].split("/"):
                res += "- {}\n".format(move)
        return res
    
    def getGender(self, trainer, pokemon, trainerI, pokemonI):
        genderRatio = self.getGenderRatio(pokemon)

        if len(genderRatio) == 1: return ""
        elif genderRatio[0] == 1: return "(M)"
        elif genderRatio[1] == 1: return "(F)"
        else:
            detailedTDocs = json.load(open("ShowdownGenerator/Platinum/platinumTrainers.json"))
            detailedTrainer = [t["pokemon"][pokemonI]["personality"] for t in detailedTDocs["trainers"] if t["trainer_name"] == trainer and t["rom_id"] == int(trainerI)][0]

            pGender = detailedTrainer % 256

            threshold = genderRatio[0] * 256 - 1

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
            else:
                # ratio is always [male%, female%]
                ratios = [float(i[:-1])/100 for i in genderRatio.replace(" female", "").replace(" male", "").split(", ")]

            # update the JSON
            genderData[pName] = ratios

            # save update
            with open("ShowdownGenerator/Platinum/PokemonData/genderRatios.json", "w") as f:
                json.dump(genderData, f)

        return ratios

    def getMoves(self, name, level):
        try:
            df = pd.read_pickle("ShowdownGenerator/Platinum/PokemonData/{}.pkl".format(name))
            col = list(df)[0]
        except:
            req = Request("https://bulbapedia.bulbagarden.net/wiki/{}_(Pok%C3%A9mon)/Generation_IV_learnset".format(name))
            req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0")
            html = urlopen(req).read().decode("utf-8")
            soup = BeautifulSoup(html, "html.parser")

            table = soup.find("table", {"class": "sortable"})

            try: 
                df = pd.read_html(io.StringIO(str(table)), displayed_only=False)[0].loc[:, ["PtHGSS", "Move"]]
                col = "PtHGSS"
            except:
                df = pd.read_html(io.StringIO(str(table)), displayed_only=False)[0].loc[:, ["Level", "Move"]]
                col = "Level"

            for i in range(df.shape[0]):
                val = df.loc[i, col]
                if val == "N/AN/A": 
                    df.loc[i, col] = -1
                else: df.loc[i, col] = int(str(val)[:len(str(val))//2])

            df = df[df.loc[:,col] != -1]
            df.to_pickle("ShowdownGenerator/Platinum/PokemonData/{}.pkl".format(name))

        moves = "".join(list(df[df.loc[:,col] <= int(level)].loc[:, "Move"].tail(4).transform(lambda x: "- " + x + "\n")))
        return moves

if __name__ == "__main__":
    PlatinumShowdown()