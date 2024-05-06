from scrapers import googleSheetScraper, pokeWebScraping

import pandas as pd
import json
import pickle as pkl
import os
from itertools import chain

# TODO scrape location data
# TODO combine route data and ruleset data to see what spread of mons I can get, maybe visualize in an excel spreadseet if possible
# TODO enable encounter tracking and make dupes clause optional since the pool of encountered mons is so low, though I could also play with it for the added challenge
# TODO      maybe make a mask? using the userEncounters df  
# TODO pokewebscraping.getencounters isn't working... possibly the bulbapedia site got revamped???

class elevationLocke():
    def __init__(self) -> None:
        # google sheet ruleset specific information
        self.ssID = "1nl-oAtNK19cbusswH7r3s_5Q-BfTwDPQIIDiTb-dJJc"
        self.ssRange = 'Groups'

        self.universalData = json.load(open("allGamesData.json", encoding="utf-8"))

        self.user = input("Would you like to begin a new game or load a current game? (respond 'New' or the name of your save file)\n> ")


        if self.user == "New":
            self.user = input("Name your save file:\n> ")
            self.initNewGame()

        else:
            self.loadGame()

        # menu
        self.mainMenu()

    def mainMenu(self):
        menuChoice = input("\nWhat would you like to do?\n1: Update encounters\n2: View encounters for a route\n3: Clear encounters\n4: View Encounters\n5: Get Encounters Spreadsheet\n6: View possible locations for an encounter\n7: Clean up data (Elevationlocke)\n> ")
        if menuChoice == "1":
            self.updateEncounters()
        elif menuChoice == "2":
            self.viewRouteEncounters()
        elif menuChoice == "3":
            self.clearEncounters()
        elif menuChoice == "4":
            self.viewEncounters()
        elif menuChoice == "5":
            self.makeEncountersSpreadsheet()
        elif menuChoice == "6": 
            self.viewEncounterOnRoutes()
        elif menuChoice == "7":
            self.cleanElevationlocke()
        else:
            pass

    def cleanElevationlocke(self):
        # need to remove mons that are banned or unelevated
        allElevatedMons = list(chain(*[self.elevationMons[elevation] for elevation in self.elevationMons.keys() if elevation != "Unelevated"]))
        self.allEncounterData = self.allEncounterData[self.allEncounterData.index.get_level_values("Pokémon").isin(allElevatedMons)]
        self.saveGame()

    def getSpeciesClauseMons(self):
        speciesClauseMons = []
        for mon in self.userEncounters["Pokémon"]:
            lineData = [line for line in self.userData["regionalEvos"] if mon in line]
            if lineData != []:
                speciesClauseMons.extend(lineData[0])
            else:
                speciesClauseMons.append(mon)
        return speciesClauseMons
    
    def makeEncountersSpreadsheet(self):
        routes = [x for x in list(self.allEncounterData.index.get_level_values("Route").unique()) if x not in list(self.userEncounters["Route"])]
        
        speciesClauseMons = self.getSpeciesClauseMons()
        pokemon = [x for x in list(self.allEncounterData.index.get_level_values("Pokémon").unique()) if x not in speciesClauseMons]
        
        evoLines = self.userData["regionalEvos"]
        data = []
        mons = []

        for mon in pokemon:
            appended = False
            for line in evoLines:
                if mon in line and "/".join(line) not in mons:
                    appended = True
                    mons.append("/".join(line))
                    monRoutes = []
                    for route in routes:
                        isPresent = False
                        routeData = self.allEncounterData[self.allEncounterData.index.get_level_values("Route") == route]
                        for mon2 in line:
                            if mon2 in list(routeData.index.get_level_values("Pokémon")):
                                monRoutes.append(True)
                                isPresent = True
                                break
                        if not isPresent: monRoutes.append("")

                    data.append(monRoutes)
                    break

                elif mon in line: 
                    appended = True
                    break

            if not appended:
                mons.append(mon)
                monRoutes = []
                for route in routes:
                    routeData = self.allEncounterData[self.allEncounterData.index.get_level_values("Route") == route]
                    if mon in list(routeData.index.get_level_values("Pokémon")):
                        monRoutes.append(True)
                    else: 
                        monRoutes.append("")

                data.append(monRoutes)
        
        df2 = pd.DataFrame(data, index=mons, columns=routes).T

        df2.to_excel("{}\encounterTable.xlsx".format(self.user))
        self.mainMenu()
    
    def viewEncounterOnRoutes(self):
        mon = input("What Pokémon would you like to see?\n> ")
        df = self.allEncounterData[self.allEncounterData.index.get_level_values("Pokémon") == mon]

        dupesBool = ~df.index.get_level_values("Route").isin(self.userEncounters["Route"])
        df = df[dupesBool]

        routeLst = list(df.index.get_level_values("Route"))
        routeFormat = "".join([routeLst[i] + ", " if i != len(routeLst) - 1 else routeLst[i] for i in range(len(routeLst))])
        print("{} is located at {}".format(mon, routeFormat))
        print(df)

        print("The full list of encounters for the above routes is {}".format(self.allEncounterData[self.allEncounterData.index.get_level_values("Route").isin(routeLst)]))

        viewMore = input("\nWould you like to view more encounters? (Y/N)\n> ")
        if viewMore == "Y": self.viewEncounterOnRoutes()
        self.mainMenu()

    def clearEncounters(self):
        clearAll = input("\nWould you like to clear all encounters? (Y/N)\n> ")
        if clearAll == "Y": 
            self.userEncounters = self.userEncounters.iloc[0:0] #pd.DataFrame(columns=self.userEncounters)
            self.saveGame()
        # TODO clear one or multiple routes at a time
        # else:
            # routeToClear = input("What route would ")

    def addEncounter(self, route, encounter):
        elevationToAdd = [x for x in self.elevationMons.keys() if encounter in self.elevationMons[x]]
        newEncounter = pd.DataFrame([encounter, route, " & ".join(elevationToAdd)]).set_index([self.userEncounters.columns]).T
        self.userEncounters = pd.concat([self.userEncounters, newEncounter], axis=0).reset_index(drop=True)
        self.saveGame()

    def printRoute(self, route):
        routeData = self.allEncounterData[self.allEncounterData.index.get_level_values("Route") == route]
        routeElevations = [" & ".join([x for x in self.elevationMons.keys() if mon in self.elevationMons[x]]) for mon in routeData.index.get_level_values("Pokémon")]
        routeElevationsBool = [True if (elevation != "" and elevation != "Unelevated") else False for elevation in routeElevations]
 
        res = routeData[routeElevationsBool].dropna(axis="columns", how="all")
        speciesClauseMons = self.getSpeciesClauseMons()
        dupesBool = ~res.index.get_level_values("Pokémon").isin(speciesClauseMons)
        res = res.assign(Dupes=["" if b else "x" for b in dupesBool]).set_index(["Dupes", res.index])

        noDupeRres = res[dupesBool]

        return res, noDupeRres

    def updateEncounters(self):
        if "Starter" not in self.userEncounters["Route"].tolist():
            starter = input("\nWhat is your starter?\n> ")
            self.addEncounter("Starter", starter)

        print("\n", self.userEncounters)
        print("\nRoutes") 
        allRoutes = pd.unique(self.allEncounterData.index.get_level_values("Route"))
        newEncounterRoutes = [x for x in allRoutes if x not in self.userEncounters["Route"].tolist()]
        print(newEncounterRoutes)

        routeToAdd = input("\nWhat route's encounter would you like to add?\n> ")
        if routeToAdd in newEncounterRoutes: 
            routeData, incDupesRouteData = self.printRoute(routeToAdd)
            print(incDupesRouteData)
            
            encounterToAdd = input("\nWhat encounter would you like to add?\n> ")
            if encounterToAdd in routeData.index.get_level_values("Pokémon"): 
                self.addEncounter(routeToAdd, encounterToAdd)
            
                addMore = input("\nWould you like to add more encounters? (Y/N)\n> ")
                if addMore == "Y":
                    self.updateEncounters()
        elif routeToAdd in allRoutes:
            # update data if mon evolves here
            pass
        
        self.mainMenu()

    def viewEncounters(self):
        print("All Encounters\n{}\n".format(self.userEncounters))
        print("Underground\n{}\n".format((self.userEncounters[self.userEncounters["Elevation Type"].str.contains("Underground")])))
        print("Waveriding\n{}\n".format(self.userEncounters[self.userEncounters["Elevation Type"].str.contains("Waveriding")]))
        print("Aeronautic\n{}\n".format(self.userEncounters[self.userEncounters["Elevation Type"].str.contains("Aeronautic")]))

        self.mainMenu()
    
    def viewRouteEncounters(self):
        # maybe update this to allow checking multiple routes at once?
        print("\nRoutes\n", pd.unique(self.allEncounterData.index.get_level_values("Route")))
        routeToView = input("What route would you like to view the encounters for?\n> ")
        
        routeData, incDupesRouteData = self.printRoute(routeToView)
        print(routeData, "\n\n", "Your potential unique encounters are:\n{}".format(incDupesRouteData))

        seeMore = input("\nWould you like to see another route? (Y/N)\n> ")
        if seeMore == "Y":
            self.viewRouteEncounters()
        else: self.mainMenu()
            
    def initNewGame(self):
        # init everything
        self.userData = {}

        # makes new folder to store all the save information
        newpath = r'C:\Users\Gil\OneDrive\Documents\Programming\Pokemon\pokemon test\{}'.format(self.user)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        # for all games
        self.evoLinesDict = pokeWebScraping.getLineData()

        # game specific information
        self.gameName = input("What game are you playing?\n> ")
        self.userData["gameName"] = self.gameName
        self.gameGen = self.universalData["Games"][self.gameName]["gameGen"]
        self.userData["gameGen"] = self.gameGen
        self.userData["abbrev"] = self.universalData["Games"][self.gameName]["Abbreviation"]
        self.userData["abbrevs"] = self.universalData[self.gameGen]["abbrevs"]

        self.bannedMons = self.universalData[self.gameGen]["Banned Mons"]
        self.userData["bannedMons"] = self.bannedMons
        
        self.regionalDex = pokeWebScraping.getRegionalDex(self.gameGen)
        self.userData["regionalDex"] = self.regionalDex
        
        self.regionalEvos = self.getRegionalEvos()
        self.userData["regionalEvos"] = self.regionalEvos

        self.regionalEvos = pd.DataFrame(self.regionalEvos, index=[x[-1] for x in self.regionalEvos]).fillna("")

        self.allEncounterData = pd.concat(self.getAllEncounterData())

        # ruleset specific scraped information
        self.elevationLines = googleSheetScraper.main(self.ssID, self.ssRange)
        colsToKeep = [x for x in self.elevationLines[0] if x != ""]
        self.elevationLines = pd.DataFrame(self.elevationLines[1:], columns=self.elevationLines[0])[colsToKeep].dropna(axis="index", how="all").fillna("")
        
        # preliminary data sorting
        self.elevationMons = self.sortLines()
        self.userData["elevationMons"] = self.elevationMons

        self.userEncounters = pd.DataFrame(columns=["Pokémon", "Route", "Elevation Type"])

        self.saveGame()

    def getAllEncounterData(self):
        id = "1e4WNHfeaPH06Jcf8_E-MDFzmihgaVpFgkcMZ2E8TQpA"
        routeRange = "Team & Encounters!I5:I65"
        routes = [r[0] for r in googleSheetScraper.main(id, routeRange)]
        region = self.universalData[self.gameGen]["Region"]

        allEncounters = []
        for i in range(len(routes)):
            r = routes[i]
            if i == 0: encounters = self.universalData[self.gameGen]["Starters"]
            else: encounters = pokeWebScraping.getRouteEncounters(r, region, self.universalData[self.gameGen]["headingDesignator"], self.userData, self.universalData)
            # this is how to filter based on index value for a multi index /// print(encounters[encounters.index.get_level_values("Area") == "Inner"])
            print(encounters)
            if isinstance(encounters, pd.DataFrame): allEncounters.append(encounters)
        
        return allEncounters

    def loadGame(self):
        self.userData = json.load(open("{}\data.json".format(self.user)))
        self.bannedMons = self.userData["bannedMons"]
        # list of all regional pokemon
        self.regionalDex = self.userData["regionalDex"]
        # list of all regional valid evolutions
        self.regionalEvos = pd.DataFrame(self.userData["regionalEvos"], index=[x[-1] for x in self.userData["regionalEvos"]]).fillna("")
        # dictionary of challenge specific categories
        self.elevationMons = self.userData["elevationMons"]
        # load encounter data
        self.allEncounterData = pd.read_pickle("{}\data.pkl".format(self.user))
        self.userEncounters = pd.read_pickle("{}\encounters.pkl".format(self.user))

    def saveGame(self):
        with open("{}\data.json".format(self.user), "w") as file:
                json.dump(self.userData, file, indent=4)

        self.allEncounterData.to_pickle("{}\data.pkl".format(self.user))
        self.userEncounters.to_pickle("{}\encounters.pkl".format(self.user))
        
    def getRegionalEvos(self):
        evoLines = list(self.evoLinesDict.keys())

        regionalEvos = []
        for line in evoLines:
            newLine = []
            for mon in line:
                if mon in self.regionalDex and mon not in newLine and mon not in self.bannedMons: newLine.append(mon)
            if len(newLine) > 1: regionalEvos.append(newLine)
        return regionalEvos

    def sortLines(self):        
        res = {category : [] for category in list(self.elevationLines.columns)}

        for mon in self.regionalDex:
            for category in list(self.elevationLines.columns):
                searchMon = self.elevationLines[self.elevationLines[category].str.contains(mon)]
                if len(searchMon.index) != 0 and mon != "":
                    # search results, a series
                    searchRes = searchMon[category]
                    # cell text
                    lineInfo = self.elevationLines[category].iloc[searchRes.index[0]-1]
                    
                    if "line" in lineInfo and lineInfo.split(" ")[0] == mon:
                        monsToAdd = list(self.regionalEvos.loc[mon])
                        for monToAdd in monsToAdd:
                            if monToAdd != "": res[category].append(monToAdd)

                    else:
                        if mon not in res[category]: res[category].append(mon)
                    
        return res

if __name__ == "__main__":
    elevationLocke()