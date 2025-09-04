import openpyxl
import pandas as pd
import json
import numpy as np
import argparse
import re
import yaml
import os

# adds the path absolutely so the code can be run from anywhere
import helper

import sys
sys.path.insert(0, helper.getAbsPath(__file__, 2))

from src.pokeapi import main as pokeapi
from src.utils.google_sheets_api import google_sheets_api


class GroupData():
    def __init__(self, routes=[], encounters=[], assignMe = {}) -> None:
        self.routes = routes
        self.encounters = encounters
        self.assignMe = assignMe

        self.flags = {
            "Honey": False
        }
    
    def __repr__(self) -> str:
        return json.dumps(self.assignMe, indent=4)

class LocalGame():
    def __init__(self, file_path) -> None:
        # open NRotM spreadsheet
        self.wb = openpyxl.load_workbook(filename = file_path)

        self.ws = self.wb["Team & Encounters"]
        
        self.routeCol = self.getCol("Location")
        self.encounterCol = self.getCol("Encounter")
        self.routeOrder = [route.value for route in self.ws[self.routeCol] if route.value not in [None, "Location"]]
        self.gameName = self.wb["Tracker"]["A1"].value

        # init pokeapi calls
        self.pokeapi = pokeapi.PokeapiAccess()
        self.pokedex = self.pokeapi.getPokedexFromRegion(self.gameName)
        self.evoLines = self.pokeapi.getEvoLinesFromPokedex(self.pokedex)

        # initialize encounter info
        self.encounterData = self.getEncounterData()
        self.encounterTable = self.getEncounterTable()

        # game specific information
        if self.gameName == "Platinum":
            self.honeyMons = ["Aipom", "Heracross", "Wurmple", "Burmy", "Combee", "Cherubi", "Munchlax"]
    
    def getCol(self, value):
        ws = self.wb["Team & Encounters"]
        for row in ws.iter_rows():
            for col in row: 
                if col.value == value: return col.column_letter

        return None
    
    def getEncounterData(self):
        res = []

        dvList = self.ws.data_validations.dataValidation
        for dv in dvList: 
            cells = [str(c) for c in list(dv.sqref.ranges) if self.encounterCol in str(c)]   # a list of CellRange elements
            
            if cells == []: continue 

            encounters = dv.formula1.replace('"', "").split(",")                            # a list of encounters

            cells = self.expandColon(cells)
            for c in cells: 
                loc = c.replace(self.encounterCol, chr(ord(self.encounterCol)-1))
                route = self.ws[loc].value
                res.extend([route, enc, 1] for enc in encounters)

        return res
    
    def expandColon(self, cells):
        res = []
        for cell in cells:
            if ":" not in cell: res.append(cell)
            else:
                start, stop = map(int, cell.replace(self.gameData.encounterCol, "").split(":"))
                while start <= stop:
                    res.append(self.gameData.encounterCol + str(start))
                    start += 1

        return res
    
    def getEncounterTable(self):
        # initial df without manipulation
        df = pd.DataFrame.from_records(self.encounterData, columns=["Route", "Encounter", "Value"]) \
                         .pivot(index="Route", columns="Encounter", values="Value") 

        return self.consolidateEvoLines(df.reindex([route for route in self.routeOrder if route in list(df.index)])).dropna(axis=0, how="all")
    
    def consolidateEvoLines(self, df):
        res = []

        for line in self.evoLines:
            relevantLine = [re.search(r"^{}".format(mon), "\n".join(df.columns), flags=re.I|re.M).group() for mon in line if re.search(r"^{}".format(mon), "\n".join(df.columns), flags=re.I|re.M)]
            if len(relevantLine) != 0:
                dfFiltered = pd.DataFrame(df[relevantLine].agg("max", axis="columns"))
                dfFiltered.columns = ["/".join(relevantLine)]
                res.append(dfFiltered)
        
        return pd.concat(res, axis=1)
    
class CloudGame():
    def __init__(self):
        # check if NRotM spreadsheet has been parsed yet

        # open NRotM spreadsheet
        # self.wb = openpyxl.load_workbook(filename = file_path)
        # self.ws = self.wb["Team & Encounters"]
        # self.routeCol = self.getCol("Location")
        # self.encounterCol = self.getCol("Encounter")
        # self.routeOrder = [route.value for route in self.ws[self.routeCol] if route.value not in [None, "Location"]]
        # self.gameName = self.wb["Tracker"]["A1"].value

        # init pokeapi calls
        self.pokeapi = pokeapi.PokeapiAccess()
        self.pokedex = self.pokeapi.getPokedexFromRegion(self.gameName)
        self.evoLines = self.pokeapi.getEvoLinesFromPokedex(self.pokedex)

        # game specific information
        if self.gameName == "Platinum":
            self.honeyMons = ["Aipom", "Heracross", "Wurmple", "Burmy", "Combee", "Cherubi", "Munchlax"]


class NRotMEncounterRouting():
    def __init__(self) -> None:
        # user can include an optional argument to check for a json file of encounters
        # config file is required
        self.parser = self.initParser()
        self.args = self.parser.parse_args()

        # read config file
        with open(self.args.config, "r") as f:
            self.run_config = yaml.safe_load(f)
        
        # get initial dataset of routes and encounters
        if self.args.cloud:
            # self.gameData = CloudGame() #TODO
            google_sheets_api.GoogleSheetsApi(self.run_config["spreadsheet_id"],
                                              self.run_config["spreadsheet_range"],
                                              self.run_config["creds_path"],
                                              self.run_config["token_path"],
                                              self.run_config["output_json_path"])
        else:         
            self.gameData = LocalGame(file_path = self.run_config["sheet_path"])

        # initialize slice history of encounter assignment
        self.encounterTables = [self.gameData.encounterTable]

        # update honey table encounters
        if self.gameData.gameName == "Platinum":
            self.gameData.honeyMons = [mon for mon in self.gameData.honeyMons if mon in self.gameData.encounterTable]

        # notes for encounter order on final spreadsheet
        self.notes = {route: {} for route in list(self.gameData.encounterTable.index)}

        # initialize assigned encounters
        self.assignedEncounters = {}
        self.assignedEncountersSlice = []
        
        # update assigned encounters if file exists
        if os.path.exists(self.run_config["encounters_path"]):
            self.importEncountersJSON(self.run_config["encounters_path"])

        if self.args.route: self.route()

    def importEncountersJSON(self, encounters_path):
        with open(encounters_path, "r") as f:
            assignMe = json.loads(f.read())
                
        routes = list(route for route in assignMe.keys() if assignMe[route] != "")
        failedRoutes = list(route for route in assignMe.keys() if assignMe[route] == "" )
        encounters = [list(self.gameData.encounterTable.filter(like=encounter, axis=1).columns)[0] for encounter in assignMe.values() if encounter != "" and list(self.gameData.encounterTable.filter(like=encounter, axis=1).columns) != []]
                
        assignMe = {routes[i]: encounters[i] for i in range(len(routes))}
        routes = routes + failedRoutes

        groupData = GroupData(assignMe=assignMe, routes=routes, encounters=encounters) 
        self.update(groupData=groupData, df=self.gameData.encounterTable, isJSON=True) 

    def initParser(self):
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required = True)
        group.add_argument("--test", "-t",
                            required = False,
                            help = "select to test manual encounter routing",
                            action = "store_true")
        group.add_argument("--route", "-r",
                            required = False,
                            help = "select to use the routing algorithm",
                            action = "store_true")
        parser.add_argument("--config", "-c",
                            required = True,
                            help = ".yaml file for configuring run data")
        parser.add_argument("--cloud", "-cl", 
                            required = False,
                            help = "toggle loading encounter data from google sheet",
                            action = "store_true")
        return parser

    def route(self):
        methods = {self.assignOneToOne: True, 
                   self.checkDuplicates: True}
        
        while True in methods.values():
            for method in methods.keys():
                methods[method] = method()

        # ask user about unique encounters before finishing?
        self.printProgress(pd.DataFrame.from_dict({"Encounter": self.assignedEncounters}), "*==")
        self.exportTable()

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
            onlyOneDict = onlyOneMelted.to_dict("split")
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
            flagHoney = True if set(encounters).issuperset(set([mon for mon in self.gameData.honeyMons if mon in workingdf.columns])) else False

            groupData = GroupData()
            # if there are more routes than encounters, each encounter can be assigned
            if len(groups[group].values) >= np.nansum(group):
                groupData.encounters = encounters
                groupData.routes = list(groups[group].values)
                groupData.assignMe = {route: " or ".join(encounters) for route in groupData.routes}
                groupData.flags["Honey"] = flagHoney
                groupsData[i] = groupData
                i += 1
        
        # check if user would like to update any group
        if len(groupsData.keys()) == 1:
            self.update(groupsData[0], workingdf)
            return True
        elif groupsData != {}:
            print(groupsData)
            groupData = groupsData.get(int(input("Which group would you like to assign?\n> ")))
            if groupData: 
                self.update(groupData, workingdf)
                return True
        else: return False

    def update(self, groupData, df, isJSON=False):
        # if honey location, get all remaining honey encounters and update
        if groupData.flags["Honey"]: 
            # update honey table encounters
            self.gameData.honeyMons = [mon for mon in self.gameData.honeyMons if mon in df]
            remainingHoneyRoutes = [index for index, row in df.iterrows() if sum(row[self.gameData.honeyMons]) == len(row[self.gameData.honeyMons]) and sum(row[self.gameData.honeyMons]) == row.sum() and index not in groupData.routes]
            flagGroupData = GroupData(remainingHoneyRoutes, self.gameData.honeyMons)
            flagGroupData.assignMe = {route: " or ".join(flagGroupData.encounters) for route in flagGroupData.routes}
            self.update(flagGroupData, df)

        # update the assigned encounter dict
        self.assignedEncounters.update(groupData.assignMe)

        # make note of routes with encounters that have been assigned
        if not isJSON:
            for mon in groupData.encounters:
                monRoutes = [route for route in df[mon][df[mon] == 1].index if route not in groupData.routes]
                for route in monRoutes:
                    passN = len(self.encounterTables)
                    currNotes = self.notes[route].get(passN)
                    if currNotes: currNotes.add(mon)
                    else: self.notes[route][passN] = set([mon])

        # remove filtered items from df
        df = df.loc[~df.index.isin(groupData.routes), ~df.columns.isin(groupData.encounters)] \
               .dropna(axis=0, how="all")
        
        # remove encounters that are no longer accessible
        self.checkAvailableEncounters(df)

        # add the updated dataframe as a slice to the results table
        self.encounterTables.append(df)
        if isJSON: self.encounterTables.pop(0)
        
        # print encounters added
        newEncounters = pd.DataFrame.from_dict(groupData.assignMe, orient="index", columns=["Encounter"])
        newEncounters["Pass"] = len(self.encounterTables) - 1
        newEncounters.index.name = "Route"
        newEncounters.set_index(["Pass", newEncounters.index], inplace = True)
        self.assignedEncountersSlice.append(newEncounters)
        self.printProgress(newEncounters)

        # return df because assignOneToOne needs the workingdf updated to continue making passes
        # alternatively could make it loop outside of the method?
        return df
    
    def checkAvailableEncounters(self, df):
        lostEncounters = df.loc[:, df.sum(axis=0) == 0]
        df.dropna(axis=1, how="all", inplace=True)
        if len(lostEncounters.columns) != 0: print("WARNING: {} ARE LOST".format(", ".join(lostEncounters.columns)))

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
        yellowFill = openpyxl.styles.PatternFill(bgColor="FFEB9C", fill_type="solid")
        yellowFont = openpyxl.styles.Font(color="9C5700")
        yellowdxf = openpyxl.styles.differential.DifferentialStyle(font=yellowFont, fill=yellowFill)

        with pd.ExcelWriter(self.run_config["output_sheet_path"]) as writer:
            # write each pass' slice as a worksheet
            for i in range(len(self.encounterTables)):
                self.encounterTables[i].to_excel(writer, sheet_name="EncounterTable{}".format(str(i)), freeze_panes=(1, 1))

                worksheet = writer.sheets["EncounterTable{}".format(str(i))]

                sheetData = list(worksheet.columns)
                # the range of the table body ignoring header row and column
                cRange = "{}:{}".format(sheetData[1][1].coordinate, sheetData[-1][-1].coordinate)

                # fills the background color
                worksheet.conditional_formatting.add(cRange, openpyxl.formatting.rule.CellIsRule(operator='equal', formula=[1], stopIfTrue=False, fill=greenFill, font=greenFont))
            
            # write the historical pass table as the final worksheet
            pd.concat(self.assignedEncountersSlice).to_excel(writer, sheet_name = "EncounterList")
            worksheet = writer.sheets["EncounterList"]
            # the range of the relevant column
            cRange = "{}:{}".format(worksheet["C"][0].coordinate, worksheet["C"][-1].coordinate)
            worksheet.conditional_formatting.add(cRange, openpyxl.formatting.rule.Rule(type="duplicateValues", dxf=yellowdxf))
            
            # add comments to each sheet to show what pokemon need to be encountered to create that instance of encounter routing
            for sheet in writer.sheets: 
                worksheet = writer.sheets[sheet]

                if not sheet.isalpha(): i = i = int("".join([char for char in sheet if char.isnumeric()]))

                if "List" in sheet: minC, maxC = 2, 2
                else: minC, maxC = 1, 1

                for col in worksheet.iter_cols(min_row = 2, min_col = minC, max_col = maxC):
                    for cell in col: 
                        routeData = self.notes[cell.value]
                        message = "\n".join(["{}: {}".format(p, ", ".join(routeData[p])) for p in range(1,i+1) if routeData.get(p)])
                        if message != "": cell.comment = openpyxl.comments.Comment(message, "openpyxl")
        return 

if __name__ == "__main__":
    NRotMEncounterRouting()