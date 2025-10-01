import sys
import os
import re
import pandas as pd
import json

sys.path.insert(0, os.path.abspath('src/ShowdownGenerator'))
import showdownPokemon
import showdownTrainer

sys.path.insert(0, os.path.abspath('src/utils'))
from scrape_learnsets import scrape_learnsets

def get_trainer_input(text):
    return input(text)

def get_trainer_n_input(text):
    return input(text)

class SMShowdown:
    def __init__(self, mode = "default") -> None:
        self.mode = mode
        self.txt = self.readTrainerData()
        self.trainer = showdownTrainer.Trainer()
        
        if self.mode == "default":
            self.main()
            self.trainer.export()

    def readTrainerData(self):
        with open(r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator\SM\trainer_data.txt", 
                 "r", encoding = 'utf-8') as f:
            res_text = f.read().split("\n")

        res = []
        counter = 0
        stopper = "======"
        temp_trainer = ""

        for row in res_text:
            if counter == 2:
                counter = 0
                res.append(temp_trainer)
                temp_trainer = ""

            if row == stopper:
                counter += 1
            else:
                temp_trainer += f"\n{row}"
        
        return res
    
    def parseTrainer(self):
        possibleTrainers = []

        while possibleTrainers == []:
            desiredTrainer = get_trainer_input("What is the trainer name?\n> ")
            
            # search for multiple versions of the same trainer
            for i in range(len(self.txt)):
                trainer_name_num = self.txt[i].split("\n")[1]
                if desiredTrainer in trainer_name_num: 
                    possibleTrainers.append(i)

            if possibleTrainers == []: 
                print("Please type a valid trainer name!")
        
        # user selects the appropriate trainer
        if len(possibleTrainers) > 1: 
            if self.mode == "default":
                for i in possibleTrainers: 
                    print(self.txt[i] + "\n")
            trainerI = int(get_trainer_n_input("Which version is correct?\n> "))
            trainer = self.txt[int(trainerI - 1)].split("\n")[1:]
        else: 
            trainer = self.txt[possibleTrainers[0]].split("\n")[1:]
            trainerI = trainer[0].split("-")[0]
        
        # updates trainer name to verify search accuracy
        desiredTrainer = trainer[0].split("- ")[-1]
        pokemonList = trainer[2:]
        self.trainer.name = desiredTrainer
        self.trainer.number = str(int(trainerI))
        self.trainer.pokemon = [showdownPokemon.Pokemon() for _ in range(len(pokemonList))]

        return pokemonList
    
    def getLevelUpMoveset(self, pokemon):
        path = r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator\SM\learnsets.json"
        # check to see if json file exists
        if not os.path.exists(path):
            # scrape all the necessary data
            scrape_learnsets("sun-moon", path)
        
        # load the four most recent moves from there
        with open(path, "r") as f:
            learnsets = json.load(f)
            pokemon_learnset = pd.DataFrame.from_dict({pokemon.name: learnsets[pokemon.name.lower().replace("’", "")]})
            pokemon_learnset.index = pokemon_learnset.index.astype(int)
            learnset_capped = pokemon_learnset[pokemon_learnset.index <= int(pokemon.level)]
            return learnset_capped.iloc[-4:, :].values.squeeze().tolist()
    
    def main(self):
        # select the trainer and extract relevant information
        pokemon_list = self.parseTrainer()

        # get pokemon data
        for i in range(len(pokemon_list)):
            pokemon = self.trainer.pokemon[i]
            pokemon_data = pokemon_list[i]

            pokemon.trainer = self.trainer.name

            # name
            pokemon.name = re.match(r".+(?=\(Lv)", pokemon_data).group(0).strip()

            # gender TODO skipping for now

            # item
            if "@" in pokemon_data:
                # checks for end of item as either parenthesis or IVs
                pokemon.item = "@ " + re.search(r"(?<=@)[a-zA-Z' ]+(?=\(|IVs)", pokemon_data).group(0).strip()

            # ivs
            iv_values = re.search(r"(?<=IVs: ).+(?= EVs)", pokemon_data).group().strip().split("/")
            pokemon.IVs = [f"{iv_value} {stat}" for iv_value, stat in zip(iv_values, ["HP", "Atk", "Def", "SpA", "SpD", "Spe"])]

            # evs
            ev_values = re.search(r"(?<=EVs: ).+$", pokemon_data).group().strip().split("/")
            pokemon.EVs = [f"{ev_value} {stat}" for ev_value, stat in zip(ev_values, ["HP", "Atk", "Def", "SpA", "SpD", "Spe"])]

            # ability
            if "Ability" in pokemon_data:
                pokemon.ability = re.search(r"(?<=Ability: )[a-zA-Z ']+", pokemon_data).group(0).strip()
        
            # level - don't need to check the sheet for this
            pokemon.level = re.search(r"(?<=\(Lv. )[0-9]+", pokemon_data).group(0).strip()
            
            # nature - only present in sheet
            pokemon.nature = re.search(r"(?<=Nature: )\w+(?=\))", pokemon_data).group().strip()

            # moves            
            moves = [m for m in re.search(r"(?<=Moves: ).+(?=\) )", pokemon_data).group(0).strip().split("/") if m != "(None)"]
                            
            if moves == []:
                moves = self.getLevelUpMoveset(pokemon)

            pokemon.moves = moves

if __name__ == "__main__":
    SMShowdown()