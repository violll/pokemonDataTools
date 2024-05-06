from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import pandas as pd

f = open("ShowdownGenerator/Platinum/Full Pokemon Platinum Trainer Data.txt", "r")
txt = f.readlines()

def formatTrainer(txt):
    desiredTrainer = input("What is the trainer name and number?\n> ")
    for i in range(len(txt)):
        if desiredTrainer in txt[i]:
            res = ""
            trainer = " ".join(txt[i].split(" ")[1:]).strip()
            count = 0
            while count < 2:
                i += 1
                pokemon = txt[i].strip()
                if "=" in pokemon:
                    count += 1
                elif "Pokemon" in pokemon: 
                    pass
                elif "Item" in pokemon: res += pokemon + "\n"
                elif pokemon != "": 
                    res += formatPokemon(pokemon, trainer) + "\n"
            print(res)
            return None
        
def formatPokemon(pokemon, trainer):
    res = ""
    attributes = pokemon.split(" ")
    name = attributes[0]
    level = attributes[2]
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

    res += "{} ({}) ({})\n".format(trainer, name, input("What gender is {}'s {}?\n> ".format(trainer, name)))
    res += "IVs: {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe\n".format(attributeDict["IVs"][0], attributeDict["IVs"][1], attributeDict["IVs"][2], attributeDict["IVs"][3], attributeDict["IVs"][4], attributeDict["IVs"][5])
    res += "Ability: {}\n".format(attributeDict["Ability"])
    res += "Level: {}\n".format(level)
    res += "{} Nature\n".format(attributeDict["Nature"])
    if attributeDict["Moves"] == "Default":
        res += getMoves(name, level)
    else: 
        for move in attributeDict["Moves"].split("/"):
            res += "- {}\n".format(move)
    return res

def getMoves(name, level):
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
            df = pd.read_html(str(table), displayed_only=False)[0].loc[:, ["PtHGSS", "Move"]]
            col = "PtHGSS"
        except:
            df = pd.read_html(str(table), displayed_only=False)[0].loc[:, ["Level", "Move"]]
            col = "Level"

        for i in range(df.shape[0]):
            val = df.loc[i, col]
            if val == "N/AN/A": 
                df.loc[i, col] = -1
            else: df.loc[i, col] = int(str(val)[:len(str(val))//2])

        df = df[df.loc[:,col] != -1]
        df.to_pickle("PokemonData/{}.pkl".format(name))

    moves = "".join(list(df[df.loc[:,col] <= int(level)].loc[:, "Move"].tail(4).transform(lambda x: "- " + x + "\n")))
    return moves

if __name__ == "__main__":
    formatTrainer(txt)