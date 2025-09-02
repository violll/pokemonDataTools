from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import requests
import json
import re

import pandas as pd

def getLineData():
    req = Request("https://pokemondb.net/evolution")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
    html = urlopen(req).read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    data = {}

    x = soup.findAll("div", {"class": "infocard-filter-block"})
    for line in x:
        mons = line.findAll("div", {"class": "infocard"})
        
        names = [mon.findAll("a", {"class": "ent-name"}) for mon in mons]
        name = [n[0].string for n in names]

        imgs = [mon.findAll("source") for mon in mons]
        img = [i[0]["srcset"] for i in imgs if i!=[]]
        if imgs[0] == []:
            imgs = [mon.findAll("img", {"class": "img-fixed img-sprite"}) for mon in mons]
            img = [i[0]["src"] for i in imgs]

        data[tuple(name)] = img

    return data

# TODO make into a nice looking excel sheet!
# to make it look nice I'll need to check for repeats and delineate that way

def getRegionalDex(gameName):
    gameName = gameName.lower().replace(" ", "").replace("&", "-")

    req = Request("https://pokemondb.net/pokedex/game/{}".format(gameName))
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
    html = urlopen(req).read().decode("utf-8")
    soup = BeautifulSoup(html, "html.parser")

    x = soup.find("div", {"class": "infocard-list infocard-list-pkmn-lg"})
    mons = x.findAll("a", {"class": "ent-name"})

    regionalDex = [mon.string for mon in mons]
    return regionalDex

def getRouteEncounters(route, region, headingDesignator, userData, universalData, routeClarifier=None):
    gameVersion = userData["gameGen"]
    userGame = userData["abbrev"]
    gameOptions = userData["abbrevs"]
    pinwheelClause = universalData[gameVersion]["Pinwheel Clause"]
    
    gameVersion = gameVersion.replace("&", "and")

    if "Route" in route:
        url = "https://bulbapedia.bulbagarden.net/wiki/{}_{}".format(region, route.replace(" ", "_"))
    elif "Victory Road" == route:
        url = "https://bulbapedia.bulbagarden.net/wiki/{}_{}".format(route.replace(" ", "_"), gameVersion.replace(" ", "_"))
    # going to ignore trades for now
    elif route == "In-game Trade":
        return None
    else:
        url = "https://bulbapedia.bulbagarden.net/wiki/{}".format(route.replace(" ", "_"))

    try:
        # the route is normal
        req = Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0")
        html = urlopen(req).read().decode("utf-8")
    except:
        # the route follows pinwheel clause and is split
        return getRouteEncounters(" ".join(route.split(" ")[:-1]), region, headingDesignator, userData, universalData, route.split(" ")[-1])
    
    soup = BeautifulSoup(html, "html.parser")

    # gets a soup of the location and any subareas
    # THIS IS WRONG!!!!!!!!!
    soupLocs = soup.find("a", attrs={"href": "#Pok.C3.A9mon"}).findNextSibling()
    
    # no special areas and it is only present in the current gameVersion
    if soupLocs == None:
        nextSibling = "h2"
        inMultipleVersions = False
        routeAreas = []
        headingDesignator = "Pokémon"
        pokemonSoup = [x.findAll("span", attrs={"class": "mw-headline", "id": "Pok.C3.A9mon"}) for x in soup.findAll(nextSibling) if x.findAll("span", attrs={"class": "mw-headline", "id": "Pok.C3.A9mon"}) != []][0][0].parent.findNextSibling()
        res = getTables(pokemonSoup, userGame, gameOptions)
        res = res.assign(Route = [route for _ in range(len(list(res.index)))]).set_index([res.index, "Route"])
    
        if "Area" in list(res.columns): res.set_index([res.index, "Area"], inplace=True)
        else: res = res.assign(Area = ["" for _ in range(len(list(res.index)))]).set_index([res.index, "Area"])
        return res

    # there are multiple areas but may not be present in multiple versions
    else:
        routeAreas = [[y.text for y in x.findAll("span", attrs={"class": "toctext"}) if gameVersion not in y.text] for x in soupLocs.findAll("li", recursive=False) if gameVersion in x.text]
    
        # not present in multiple versions
        if routeAreas == []:
            routeAreas = [x.text for x in soupLocs.findAll("span", attrs={"class": "toctext"})]
            inMultipleVersions = False
            nextSibling = "h3"
            headingDesignator = routeAreas[0]
        else: 
            routeAreas = routeAreas[0]
            inMultipleVersions = True
            nextSibling = "h4"
            
    if route in list(pinwheelClause.keys()):
        routeAreasBool = [True if x in pinwheelClause[route][str(routeClarifier)] else False for x in routeAreas]
    elif routeClarifier != None and routeClarifier != "Gift": 
        routeAreasBool = [True if routeClarifier in x else False for x in routeAreas]
    else: routeAreasBool = [True for _ in routeAreas]
        
    # get all h3 headings that have the game designator
    pokemonSoup = soup.find("span", attrs={"class": "mw-headline", "id": "Pok.C3.A9mon"}).parent.findNextSiblings("h3")

    # check if the heading matches the correct designator
    updated = False
    tables = []
    # pinwheel clause
    if routeAreasBool != [] and routeAreasBool.count(True) == 1:
        for designator in pokemonSoup:
            if designator.text == headingDesignator:
                if inMultipleVersions: locationHeadings = designator.findNextSiblings(nextSibling)
                else: locationHeadings = [designator] + designator.findNextSiblings(nextSibling)
                for i in range(len(routeAreasBool)):
                    if routeAreasBool[i]:
                        pokemonSoup = locationHeadings[i].findNextSibling("table")
                        updated = True
                        break
            if updated: break

    elif routeAreasBool != []:
        for designator in pokemonSoup:
            if designator.text == headingDesignator:
                updated = True
                if inMultipleVersions: locationHeadings = designator.findNextSiblings(nextSibling)
                else: locationHeadings = [designator] + designator.findNextSiblings(nextSibling)
                for i in range(len(routeAreasBool)):
                    if routeAreasBool[i]:
                        tables.append(locationHeadings[i].findNextSibling("table"))
            if updated: break

    # not pinwheel clause routes with only one area
    else: 
        for designator in pokemonSoup:
            if designator.text == headingDesignator:
                pokemonSoup = designator.findNextSibling("table")
                break

    # add label if multiple sub areas are in a location
    if len(tables) > 1: 
        res = []
        locationHeadings = [locationHeadings[i] for i in range(len(routeAreas)) if routeAreasBool[i]]
        for t in tables:
            tempRes = getTables(t, userGame, gameOptions)
            tempRes["Area"] = [locationHeadings[tables.index(t)].text.replace(" area", "") for _ in range(len(tempRes.index))]
            res.append(tempRes)
        res = pd.concat(res)
    
    else:
        res = getTables(pokemonSoup, userGame, gameOptions)
    
    res.name = route
    if routeClarifier == "Gift":
        res = res.xs("Gift Pokémon", level=1, drop_level=False)

    elif routeClarifier != None:
        # check if area already exists here
        if "Area" not in list(res.columns):
            res["Area"] = [routeClarifier for _ in range(len(res.index))]    

    if routeClarifier != None: res = res.assign(Route = [route + " " + routeClarifier for _ in range(len(list(res.index)))]).set_index([res.index, "Route"])
    else: res = res.assign(Route = [route for _ in range(len(list(res.index)))]).set_index([res.index, "Route"])

    if "Area" in list(res.columns): 
        res.set_index([res.index, "Area"], inplace=True)
    else: res = res.assign(Area = ["" for _ in range(len(list(res.index)))]).set_index([res.index, "Area"])

    return res

def getTables(pokemonSoup, userGame, gameOptions):
    df = pd.read_html(str(pokemonSoup), index_col=0)[0]
    df = df[df.index.notnull()]

    df = df[["Location", "Levels", "Rate"]]

    if "Swarm" in list(df.index): 
        swarmCutoff = list(df.index).index("Swarm") 
        df = df.iloc[:swarmCutoff]
    
    # checks if there are seasonal encounters in the route
    if type(df.columns) == pd.MultiIndex and list(df.columns)[2][1] == "Sp":
        if len(df.columns.names) > 2: df = df.droplevel(df.columns.names[-1], axis=1)
        seasonRates = df["Rate"]
        df.columns = df.columns.map(lambda x: x[0]) 
        df = df.loc[:,~df.columns.duplicated()].copy()
    elif type(df.columns) == pd.MultiIndex:
        df = df.droplevel(df.columns.names[1], 1)
        seasonRates = False
        df = df.T.drop_duplicates().T
    else: 
        seasonRates = False
        df = df.T.drop_duplicates().T

    # gets the indices where the headings are
    if type(seasonRates) != bool: locHeadingsBool = ~df["Rate"].str.contains("%|One|-|Fossil")
    else: locHeadingsBool = ~df["Rate"].str.contains("%|One|Fossil")

    locHeadings = locHeadingsBool.index[locHeadingsBool==True].tolist()

    if type(seasonRates) != bool: df = formatTable(locHeadings, df, True, pokemonSoup, userGame, gameOptions)
    else: df = formatTable(locHeadings, df, False, pokemonSoup, userGame, gameOptions)
    newIndex = df.index
    df = df.reset_index(drop=True)

    if type(seasonRates) != bool: 
        seasonDF = seasonRates[seasonRates.iloc[:, -1].str.contains("%|One|Fossil|-")]
        labelsToShow = getValidMons(pokemonSoup, seasonDF, userGame, gameOptions)
        seasonDF = seasonDF.loc[labelsToShow]
        seasonDF = seasonDF.reset_index(drop=True)
        df = pd.concat([df, seasonDF], axis=1).set_index([newIndex, "Location", "Levels"]).iloc[:, 1:]
        df.columns.name = "Rate"

    else: df = df.set_index([newIndex, "Location", "Levels"])

    return df

def formatTable(locHeadings, df, isSeason, pokemonSoup, userGame, gameOptions):
    dfLst = [df[:locHeadings[0]].iloc[:-1]]

    for i in range(len(locHeadings)-1):
        dfLst.append(df[locHeadings[i]:locHeadings[i+1]].iloc[:-1].assign(Location=locHeadings[i]))

    dfLst.append(df[locHeadings[-1]:].assign(Location=locHeadings[-1]))

    df = pd.concat(dfLst)

    if isSeason: df = df[df.iloc[:, -1].str.contains("%|One|-|Fossil")]
    else: df = df[df.iloc[:, -1].str.contains("%|One|Fossil")]

    labelsToShow = getValidMons(pokemonSoup, df, userGame, gameOptions)
    df = df.loc[labelsToShow]

    return df

def getValidMons(pokemonSoup, df, userGame, gameOptions):
    labelsToShow = []

    test = [i.findAll("a", {"title": re.compile("Pokémon")}) for i in pokemonSoup.findAll("tr")[1:] if i.findAll("a", {"title": re.compile("Pokémon")}) != []]
    newTest = [[x.string for x in i if x.get("class") != "image" and x.text !=""] for i in test]
    x = 0
    while x < len(newTest):
        i = newTest[x]

        if i == []: 
            newTest.remove(i)
        else:
            if x % 2 != 0:
                pass
            else:
                if i[-1] not in gameOptions:
                    i.pop()
                    del newTest[x+2]  
        x += 1

    test = newTest

    newMonData = []
    for i in range(0, len(test), 2): 
        data = test[i]
        name = " ".join(test[i+1])
        newMonData.append({name: data[len(test[i+1]):]})

    labelsToShow = []
    for d in newMonData:
        mon = list(d.keys())[0]
        if mon in " ".join(list(df.index)):
            if userGame in d[mon]:
                labelsToShow.append(True)
            else: 
                labelsToShow.append(False)
    return labelsToShow


# print(getRouteEncounters("Route 7", "Unova", "Pokémon Black and White", json.load(open("data.json")), json.load(open("allGamesData.json"))))
# print(getRouteEncounters("Icirrus City", "Unova", "Pokémon Black and White", json.load(open("data.json")), json.load(open("allGamesData.json"))))