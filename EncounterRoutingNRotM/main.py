import openpyxl
import openpyxl.comments
import openpyxl.formatting
import openpyxl.styles
import pandas as pd
import copy as cp

class NRotMEncounterRouting():
    def __init__(self) -> None:
        self.wb = openpyxl.load_workbook(filename = "EncounterRoutingNRotM/NRotM August 2024 - Platinum Healless Typeban v1.0.xlsx")
        self.ws = self.wb["Team & Encounters"]

        # SPECIFIC TO THIS SHEET
        self.relevantCol = "J"

        self.encounterData = self.getEncounterData()
        self.encounterTable = self.getEncounterTable()

        self.assignedEncounters = {}
        self.notes = {route: [] for route in list(self.encounterTable.index)}

        self.encounterTables = [self.encounterTable]

        self.assignOneToOne()
        self.exportTable()

    def getEncounterData(self):
        res = []

        dvList = self.ws.data_validations.dataValidation
        for dv in dvList: 
            cells = [str(c) for c in list(dv.sqref.ranges) if self.relevantCol in str(c)]   # a list of CellRange elements
            
            if cells == []: continue 

            encounters = dv.formula1.replace('"', "").split(",")                            # a list of encounters

            cells = self.expandColon(cells)
            for c in cells: 
                loc = c.replace(self.relevantCol, chr(ord(self.relevantCol)-1))
                route = self.ws[loc].value
                # print("{} are available at {}".format(", ".join(encounters), route))
                res.extend([route, enc, 1] for enc in encounters)

        return res

    def expandColon(self, cells):
        res = []
        for cell in cells:
            if ":" not in cell: res.append(cell)
            else:
                start, stop = map(int, cell.replace(self.relevantCol, "").split(":"))
                while start <= stop:
                    res.append(self.relevantCol + str(start))
                    start += 1

        return res

    def getEncounterTable(self):
        # initial df without manipulation
        df = pd.DataFrame.from_records(self.encounterData, columns=["Route", "Encounter", "Value"]) \
                         .pivot(index="Route", columns="Encounter", values="Value").fillna(0)
        
        return self.consolidateTrees(df)

    def consolidateTrees(self, df):
        # TEMP replace with evo lines when I have wifi again
        tempEvoLines = [["Abomasnow", "Snover"],
                        ["Azumarill", "Marill", "Azurill"],
                        ["Beautifly", "Cascoon", "Silcoon", "Wurmple"],
                        ["Buizel", "Floatzel"],
                        ["Burmy", "Wormadam", "Mothim"],
                        ["Cherubi", "Cherrim"],
                        ["Chimecho", "Chingling"],
                        ["Combee", "Vespiquen"],
                        ["Cranidos", "Rampardos"],
                        ["Carnivine"],
                        ["Drifloon", "Drifblim"],
                        ["Dusclops", "Duskull", "Dusknoir"],
                        ["Eevee"],
                        ["Feebas", "Milotic"],
                        ["Finneon", "Lumineon"],
                        ["Goldeen", "Seaking"],
                        ["Golduck", "Psyduck"],
                        ["Heracross"],
                        ["Houndour", "Houndoom"],
                        ["Ralts", "Kirlia", "Gallade", "Gardevoir"],
                        ["Kricketune", "Kricketot"],
                        ["Machop", "Machoke", "Machamp"],
                        ["Magikarp", "Gyarados"],
                        ["Magby", "Magmar", "Magmortar"],
                        ["Mantyke", "Mantine"],
                        ["Medicham", "Meditite"],
                        ["Mr-Mime"],
                        ["Nosepass", "Probopass"],
                        ["Octillery", "Remoraid"],
                        ["Pelipper", "Wingull"],
                        ["Ponyta", "Rapidash"],
                        ["Riolu", "Lucario"],
                        ["Scyther", "Scizor"],
                        ["Shellos", "Gastrodon"],
                        ["Sneasel", "Weavile"],
                        ["Sudowoodo", "Bonsly"],
                        ["Swablu", "Altaria"],
                        ["Tangela", "Tangrowth"],
                        ["Tropius"],
                        ["Unown"],
                        ["Yanma", "Yanmega"]]
        
        res = []

        for evoline in tempEvoLines:
            evoline = [mon for mon in evoline if mon in df.columns]
            test = pd.DataFrame(df[evoline].agg("max", axis="columns"))
            test.columns = ["/".join(evoline)]
            res.append(test)
            
        return pd.concat(res, axis=1)

    def assignOneToOne(self):
        workingdf = self.encounterTables[-1].copy(deep=True)

        onlyOneBool = workingdf.sum(axis=1) == 1
        
        while onlyOneBool.any():
            # get routes with only one eligible encounter (pd.DataFrame)
            # filter out the irrelevant encounters 
            onlyOneOptions = workingdf[onlyOneBool].replace(0, pd.NA) \
                                                   .dropna(axis=1, how="all")

            # melt to pd.DataFrame (index: routes, column: encounter)
            onlyOneMelted = pd.melt(onlyOneOptions, ignore_index=False, var_name="Encounter").dropna()[["Encounter"]]

            self.printProgress(onlyOneMelted)

            # drop duplicates and update the encounter dict
            self.assignedEncounters.update(onlyOneMelted.drop_duplicates().to_dict()["Encounter"])

            # make note of routes with encounters that have been assigned
            for mon in onlyOneOptions.columns:
                monRoutes = list(workingdf[mon][workingdf[mon] != 0].index)
                monRoutes = [route for route in workingdf[mon][workingdf[mon] != 0].index if route not in list(onlyOneOptions.index)]
                for route in monRoutes:
                    self.notes[route].append(mon)     
            
            # remove the filtered items from the working dataframe
            workingdf = workingdf.loc[~workingdf.index.isin(list(onlyOneOptions.index)), ~workingdf.columns.isin(onlyOneOptions.columns)]
            
            # add the updated dataframe as a slice to the results table
            self.encounterTables.append(workingdf)

            onlyOneBool = workingdf.sum(axis=1) == 1 

        self.printProgress(pd.DataFrame.from_dict({"Encounter": self.assignedEncounters}), "*==")

        return 
    
    def printProgress(self, df, pattern="="):
        print(pattern*(50//len(pattern)) + pattern[:50%len(pattern)])
        print("Final Updated Encounters")
        print(df)
        print(pattern*(50//len(pattern)) + pattern[:50%len(pattern)], "\n")

    def exportTable(self):
        # REMOVE HASHES FROM COLORS TO MAKE THEM USABLE
        greenFill = openpyxl.styles.PatternFill(bgColor='c6efce', fill_type='solid')
        greenFont = openpyxl.styles.Font(color="006100")

        with pd.ExcelWriter("EncounterRoutingNRotM/encounters.xlsx") as writer:
            for i in range(len(self.encounterTables)):
                self.encounterTables[i].to_excel(writer, sheet_name="EncounterTable{}".format(str(i)), freeze_panes=(1, 1))

                worksheet = writer.sheets["EncounterTable{}".format(str(i))]

                # fills the background color
                worksheet.conditional_formatting.add("B2:BN56", openpyxl.formatting.rule.CellIsRule(operator='equal', formula=[1], stopIfTrue=False, fill=greenFill, font=greenFont))
                # worksheet.alignment = openpyxl.styles.alignment.Alignment(horizontal="center") TODO align all rows
                # worksheet.column_dimensions["A"].bestFit = True TODO autofit the column lenghths https://stackoverflow.com/questions/13197574/openpyxl-adjust-column-width-size

            # add comments to last sheet to show what pokemon need to be encountered first
            for col in worksheet.iter_cols(min_row = 2, max_col = 1):
                for cell in col: 
                    message = ", ".join(self.notes[cell.value])
                    if message != "": cell.comment = openpyxl.comments.Comment(message, "openpyxl")
            
        return 

if __name__ == "__main__":
    NRotMEncounterRouting()