import pandas as pd

def getShowdownData():
    iris = False

    trainerName = input("What is the name of the trainer?\n> ")
    if "Iris" in trainerName: 
        trainerName = trainerName.replace("Iris", "Drayden")
        iris = True

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

            try: trainerDf = trainerDf.xs(int(trainerNum), axis="index", level="Battle", drop_level=False)
            except: print("Type a valid battle number!")
    
    for mon in trainerDf.itertuples():
        # line 1
        if iris: print("{} ({}) ({})".format(mon[0][1].replace("Drayden", "Iris"), mon.Pokemon, "F"), end=" ")
        else: 
            print("{} ({})".format(mon[0][1], mon.Pokemon), end=" ")
        
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
        for i in range(7,11): 
            move = mon[i]
            if move != "--" and type(move) != float: print("- {}".format(move))
        
        print("\n")

    return None


if __name__ == "__main__":
    getShowdownData()