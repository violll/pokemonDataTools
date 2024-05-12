import pandas as pd

def getShowdownData():
    df = pd.read_excel("ShowdownGenerator/Black&White/Pokémon Black Trainer info (Lillipup).xlsx", sheet_name=0, index_col=list(range(0,6)))
    df = df.loc[:, :"Spe"]

    trainerName = input("What is the name of the trainer?\n> ")
    trainerDf = df.loc[df.index.get_level_values(1).str.contains(trainerName)]
    potentialTrainerNums = {x[0] for x in trainerDf.index}

    if len(potentialTrainerNums) > 1:
        print(trainerDf)

        trainerNum = input("what is the number of the battle?\n> ")
        trainerDf = trainerDf.xs(int(trainerNum), axis="index", level="Battle")

    for row in trainerDf.index: 
        mon = trainerDf.loc[row]
        mon.index = [x.strip() for x in mon.index]

        # print(mon, mon.index)

        # line 1
        if mon.Item != "None": print("{} @ {}".format(mon.Pokemon, mon.Item))
        else: print(mon.Pokemon)

        # line 2
        print("Level: {}".format(mon.Level))

        # line 3
        print("{} Nature".format(mon.Nature))

        # line 4
        print("Ability: {}".format(mon.Ability))

        # line 5
        print("IVs: {} HP / {} Atk / {} Def / {} SpA / {} SpD / {} Spe".format(*[mon.IVs for _ in range(6)]))

        # moves
        for i in range(1,5): 
            move = mon["Move {}".format(i)]
            if move != "--": print("- {}".format(move))
        
        print("\n")
    return None


if __name__ == "__main__":
    getShowdownData()