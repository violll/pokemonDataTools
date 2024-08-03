import openpyxl
import pandas as pd
import json
import numpy as np

class GroupData():
    def __init__(self, routes=[], encounters=[], assignMe = {}) -> None:
        self.routes = routes
        self.encounters = encounters
        self.assignMe = assignMe
    
    def __repr__(self) -> str:
        return json.dumps(self.assignMe, indent=4)

class NRotMEncounterRouting():
    def __init__(self) -> None:
        # SPECIFIC TO THIS SHEET
        self.wb = openpyxl.load_workbook(filename = "EncounterRoutingNRotM/NRotM August 2024 - Platinum Healless Typeban v1.0.xlsx")
        self.ws = self.wb["Team & Encounters"]
        self.relevantCol = "J"
        self.routeOrder = [route.value for route in self.ws["I"] if route.value not in [None, "Location"]]

        self.encounterData = self.getEncounterData()
        self.encounterTable = self.getEncounterTable()

        self.assignedEncounters = {}
        self.notes = {route: [] for route in list(self.encounterTable.index)}

        self.encounterTables = [self.encounterTable]

        self.route()

    def route(self):
        methods = {self.assignOneToOne: True, 
                   self.checkDuplicates: True}
        
        while True in methods.values():
            for method in methods.keys():
                methods[method] = method()

        self.printProgress(pd.DataFrame.from_dict({"Encounter": self.assignedEncounters}), "*==")
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
                         .pivot(index="Route", columns="Encounter", values="Value") 

        df = self.consolidateTrees(df.reindex([route for route in self.routeOrder if route in list(df.index)])).dropna(axis=0, how="all")

        return df

    def consolidateTrees(self, df):
        # TEMP replace with evo lines when I have wifi again
        tempEvoLines = [["Abomasnow", "Snover"],
                        ["Abra", "Kadabra", "Alakazam"],
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
        assigned = False
        workingdf = self.encounterTables[-1].copy(deep=True)

        onlyOneBool = workingdf.sum(axis=1) == 1
        
        while onlyOneBool.any():
            assigned = True
            # get routes with only one eligible encounter (pd.DataFrame)
            # filter out the irrelevant encounters 
            onlyOneOptions = workingdf[onlyOneBool].replace(0, pd.NA) \
                                                   .dropna(axis=1, how="all")

            # melt to pd.DataFrame (index: routes, column: encounter)
            onlyOneMelted = pd.melt(onlyOneOptions, ignore_index=False, var_name="Encounter").dropna()[["Encounter"]]

            # do I need to drop duplicates? I can only get the encounter on one route but it doesn't matter which one
            onlyOneDict = onlyOneMelted.drop_duplicates().to_dict("split")
            groupData = GroupData(routes = onlyOneDict["index"], 
                                  encounters = list(map(lambda x: x[0], onlyOneDict["data"])),
                                  assignMe = {onlyOneDict['index'][i]: onlyOneDict['data'][i][0] for i in range(len(onlyOneDict["index"]))}
                                  )
                        
            workingdf = self.update(groupData, workingdf)

            onlyOneBool = workingdf.sum(axis=1) == 1 

        return assigned
    
    def checkDuplicates(self):
        workingdf = self.encounterTables[-1].copy(deep=True)
        relevantdf = workingdf[workingdf.duplicated(keep=False)]
        groups = relevantdf.groupby(by=list(relevantdf.columns), sort=False).groups
        
        # collect eligible group data and ask the player which group to assign
        groupsData = {}
        i = 0
        for group in groups:
            encounters = [relevantdf.columns[i] for i in range(len(relevantdf.columns)) if group[i] == 1]
            groupData = GroupData()
            # if there are more routes than encounters, each encounter can be assigned
            if len(groups[group].values) >= np.nansum(group):
                groupData.encounters = encounters
                groupData.routes = list(groups[group].values)
                groupData.assignMe = {route: " or ".join(encounters) for route in groupData.routes}
                groupsData[i] = groupData
                i += 1
        
        # check if user would like to update any group
        if groupsData != {}:
            print(groupsData)
            groupData = groupsData.get(int(input("Which group would you like to assign?\n> ")))
            if groupData: 
                self.update(groupData, workingdf)
                return True
        
        return False

    def update(self, groupData, df):
        # update the assigned encounter dict
        self.assignedEncounters.update(groupData.assignMe)

        # make note of routes with encounters that have been assigned
        for mon in groupData.encounters:
            monRoutes = [route for route in df[mon][df[mon] == 1].index if route not in groupData.routes]
            for route in monRoutes:
                self.notes[route].append(mon) 

        # remove filtered items from df
        df = df.loc[~df.index.isin(groupData.routes), ~df.columns.isin(groupData.encounters)] \
               .dropna(axis=0, how="all")

        # add the updated dataframe as a slice to the results table
        self.encounterTables.append(df)
        
        # print encounters added
        self.printProgress(pd.DataFrame.from_dict(groupData.assignMe, orient="index", columns=["Encounter"]))

        # return df because assignOneToOne needs the workingdf updated to continue making passes
        # alternatively could make it loop outside of the method?
        return df


    def printProgress(self, df, pattern="="):
        print(pattern*(50//len(pattern)) + pattern[:50%len(pattern)],
              "Update {}:".format(len(self.encounterTables) - 1) if pattern == "=" else "Final Encounters:",
              df,
              pattern*(50//len(pattern)) + pattern[:50%len(pattern)], "\n",
              sep="\n"
              )

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