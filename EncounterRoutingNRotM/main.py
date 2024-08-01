import openpyxl
import openpyxl.formatting
import openpyxl.styles
import pandas as pd

class NRotMEncounterRouting():
    def __init__(self) -> None:
        self.wb = openpyxl.load_workbook(filename = "EncounterRoutingNRotM/NRotM August 2024 - Platinum Healless Typeban v1.0.xlsx")
        self.ws = self.wb["Team & Encounters"]

        # SPECIFIC TO THIS SHEET
        self.relevantCol = "J"
        self.encounters = self.ws["J5:J64"]

        self.assignedEncounters = {}

        self.encounterData = self.getEncounterData()
        self.encounterTable = self.getEncounterTable()

        self.encounterTables = [self.encounterTable]

        # self.assignOneToOne()
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
        
        return df

    def consolidateTrees(self):
        # TEMP replace with evo lines when I have wifi again
        tempEvoLines = [["Abombasnow", "Snover"],
                        ["Asumarill", "Marill", "Azurill"],
                        ["Beautifly", "Cascoon", "Silcoon", "Wurmple"],
                        ["Buizel", "Floatzel"],
                        ["Burmy", "Wormadam", "Mothim"],
                        ["Cheribi", "Cherrim"],
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

    def assignOneToOne(self):
        workingdf = self.encounterTables[-1].copy(deep=True)

        options = workingdf.sum(axis=1) == 1
        
        while options.any():
            onlyOneOption = workingdf[options]
            onlyOneOptions = onlyOneOption.replace(0, pd.NaT).dropna(axis=1, how="all")

            print(onlyOneOptions)

            for route in onlyOneOptions.iterrows():
                encounter = route[1][route[1] == 1]
                if encounter.index[0] not in self.assignedEncounters.keys():
                    self.assignedEncounters[encounter.index[0]] = encounter.name
            
            workingdf = workingdf.filter(items=set(workingdf.columns).difference(set(onlyOneOptions.columns)), axis=1) \
                                 .filter(items=set(workingdf.index).difference(set(onlyOneOptions.index)), axis=0)
            
            print(workingdf.columns,workingdf.index)

            self.encounterTables.append(workingdf)

            options = workingdf.sum(axis=1) == 1

        print(self.assignedEncounters)
        # would want to highlight the route after removing the column so you know there's another encounter to get beforehand?

        return 

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

        return 

if __name__ == "__main__":
    NRotMEncounterRouting()