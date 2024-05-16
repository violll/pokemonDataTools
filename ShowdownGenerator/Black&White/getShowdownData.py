import pandas as pd

def getShowdownData():
    trainerName = input("What is the name of the trainer?\n> ").replace("Iris", "Drayden")
    sheetName = "Snivy"

    # if trainer is a rival, ask what the starter is
    if "Cheren" in trainerName or "Bianca" in trainerName:
        sheetName = input("What was your starter pokemon?\n> ")

    df = pd.read_excel("ShowdownGenerator/Black&White/Pokémon Black Trainer info (Lillipup).xlsx", sheet_name=sheetName, index_col=list(range(0,5)))
    df = df.loc[:, :"IVs"]

    trainerDf = df.loc[df.index.get_level_values(1).str.contains(trainerName)]
    potentialTrainerNums = {x[0] for x in trainerDf.index}

    if len(potentialTrainerNums) > 1:
        trainerNum = -1
        print(trainerDf)

        while trainerNum not in potentialTrainerNums:
            trainerNum = int(input("what is the number of the battle?\n> "))

            try: trainerDf = trainerDf.xs(int(trainerNum), axis="index", level="Battle")
            except: print("Type a valid battle number!")
    
    for mon in trainerDf.itertuples():
        # line 1
        print("{} ({})".format(mon[0][0], mon.Pokemon), end=" ")
        if mon.Gender != "--": print("({}) ".format(mon.Gender.replace("Male", "M").replace("Female", "F")), end=" ")
        if type(mon.Item) != float: print("@ {}".format(mon.Pokemon, mon.Item))
        else: print()

        # line 2
        print("Level: {}".format(mon.Level))

        # line 3
        if type(mon.Nature) != float: print("{} Nature".format(mon.Nature))

        # line 4
        print("Ability: {}".format(mon.Ability))

        # line 5
        print("IVs: {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe".format(*[mon.IVs for _ in range(6)]))

        # moves
        for i in range(6,10): 
            move = mon[i]
            if move != "--" and type(move) != float: print("- {}".format(move))
        
        print("\n")

    return None


if __name__ == "__main__":
    getShowdownData()