import sys
import os
import re
import pandas as pd

sys.path.insert(0, os.path.abspath('src/ShowdownGenerator'))
import showdownPokemon, showdownTrainer

def get_trainer_input(text):
    return input(text)

def get_trainer_n_input(text):
    return input(text)
class XYShowdown:
    def __init__(self, mode = "default") -> None:
        self.mode = mode
        self.txt, self.df = self.readTrainerData()
        self.trainer = showdownTrainer.Trainer()
        
        if self.mode == "default":
            self.main()
            self.trainer.export()

    def readTrainerData(self):
        with open(r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator\XY\TrainerData.txt", 
                 "r", encoding = 'utf-8') as f:
            res_text = f.read().split("\n\n")[1:]

        df = pd.read_excel(r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\ShowdownGenerator\XY\X_YSheet.xlsx",
                           sheet_name="Trainer stats",
                           index_col= [0, 1])
        
        return res_text, df
    
    def parseTrainer(self):
        possibleTrainers = []

        while possibleTrainers == []:
            desiredTrainer = get_trainer_input("What is the trainer name?\n> ")
            
            # search for multiple versions of the same trainer
            for i in range(len(self.txt)):
                trainer_name_num = self.txt[i].split("\n")[1]
                if desiredTrainer in trainer_name_num: possibleTrainers.append(i)

            if possibleTrainers == []: print("Please type a valid trainer name!")
        
        # user selects the appropriate trainer
        if len(possibleTrainers) > 1: 
            if self.mode == "default":
                for i in possibleTrainers: print(self.txt[i] + "\n")
            trainerI = int(get_trainer_n_input("Which version is correct?\n> "))
            trainer = self.txt[int(trainerI - 1)].split("\n")[1:]
        else: 
            trainer = self.txt[possibleTrainers[0]].split("\n")[1:]
            trainerI = trainer[0].split("-")[0]
        
        # updates trainer name to verify search accuracy
        print(trainerI)
        desiredTrainer = trainer[0].split("- ")[-1]
        pokemonList = trainer[3:]
        self.trainer.name = desiredTrainer
        self.trainer.number = str(int(trainerI))
        self.trainer.pokemon = [showdownPokemon.Pokemon() for _ in range(len(pokemonList))]

        return pokemonList
    
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

            # check the sheet before checking the text as the sheet is more accurate (I think)


            # item
            if "@" in pokemon_data:
                # checks for end of item as either parenthesis or IVs
                pokemon.item = "@ " + re.search(r"(?<=@)[a-zA-Z' ]+(?=\(|IVs)", pokemon_data).group(0).strip()

            # ivs
            iv_value = re.search(r"(?<=IVs: All )[0-9]+", pokemon_data).group(0).strip()
            pokemon.ivs = [f"{iv_value} {stat}" for stat in ["HP", "Atk", "Def", "SpA", "SpD", "Spe"]]
            
            # ability
            if "Ability" in pokemon_data:
                pokemon.ability = re.search(r"(?<=Ability: )[a-zA-Z ']+", pokemon_data).group(0).strip()
        
            # level
            pokemon.level = re.search(r"(?<=\(Lv. )[0-9]+", pokemon_data).group(0).strip()
            
            # nature TODO, only present in the sheet

            # moves
            if "Moves" in pokemon_data:
                pokemon.moves = re.search(r"(?<=Moves: )[a-zA-Z0-9' /-]+(?=\))", pokemon_data).group(0).strip().split(" / ")

        pass

if __name__ == "__main__":
    XYShowdown()