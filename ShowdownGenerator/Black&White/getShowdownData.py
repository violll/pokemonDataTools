import pandas as pd

def getShowdownData():
    trainerName = input("What is the name of the trainer?\n> ")

    sheetName = "Snivy"

    # if trainer is a rival, ask what the starter is
    if "Cheren" in trainerName or "Bianca" in trainerName:
        userStarter = input("What was your starter pokemon?\n> ")
        if userStarter == "Oshawott": 
            sheetName = "Oshawott"
        elif userStarter == "Tepig": 
            sheetName = "Tepig"
        else: sheetName = "Snivy"

    df = pd.read_excel("ShowdownGenerator/Black&White/Pokémon Black Trainer info (Lillipup).xlsx", sheet_name=sheetName, index_col=list(range(0,5)))
    df = df.loc[:, :"IVs"]

    trainerDf = df.loc[df.index.get_level_values(1).str.contains(trainerName)]
    potentialTrainerNums = {x[0] for x in trainerDf.index}

    if len(potentialTrainerNums) > 1:
        print(trainerDf)

        trainerNum = input("what is the number of the battle?\n> ")
        trainerDf = trainerDf.xs(int(trainerNum), axis="index", level="Battle")
    
    for mon in trainerDf.itertuples(index=False):
        # line 1
        print(mon.Pokemon, end=" ")
        if mon.Gender != "--": print("({}) ".format(mon.Gender.replace("Male", "M").replace("Female", "F")), end=" ")
        if type(mon.Item) != float: print("@ {}".format(mon.Pokemon, mon.Item))
        else: print()

        # line 2
        print("Level: {}".format(mon.Level))

        # line 3
        print("{} Nature".format(mon.Nature))

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