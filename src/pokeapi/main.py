import requests_cache
import json
import re

# adds the path absolutely so the code can be run from anywhere
from pathlib import Path
import sys
path = str(Path(Path(Path(__file__).parent.absolute()).parent.absolute()).parent.absolute())
sys.path.insert(0, path)

BASE_URL = "https://pokeapi.co/api/v2/"
BASE_POKEMON = "https://pokeapi.co/api/v2/pokemon/{id or name}/"
BASE_FORMS = "https://pokeapi.co/api/v2/pokemon-form/{id or name}/"
BASE_LOCATIONS = "https://pokeapi.co/api/v2/pokemon/{id or name}/encounters"
BASE_VERSIONS = "https://pokeapi.co/api/v2/version/{id or name}/"
BASE_VERSION_GROUPS = "https://pokeapi.co/api/v2/version-group/{id or name}"
BASE_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/{id or name}/"

class PokeapiAccess():
    def __init__(self) -> None:
        # initialize the session
        self.session = requests_cache.CachedSession()
        self.placeholder = "{id or name}"   # placeholder to substitute data for api calls in the BASE_ global variables

        self.versions = self.getVersions()  # list of valid game versions to call

    def getVersions(self):
        versionsResponse = self.get(BASE_VERSIONS + "?limit=none").json()
        res = [entry["name"] for entry in versionsResponse["results"]]
        while versionsResponse["next"]:
            versionsResponse = self.get(versionsResponse["next"]).json()
            res.extend([entry["name"] for entry in versionsResponse["results"]])
        return res
    
    def get(self, url, modifier=""):
        response = self.session.get(url.replace(self.placeholder, modifier))
        return response
    
    def pprint(self, data):
        print(json.dumps(data, indent=4))

    # ensure version name is formatted correctly by checking against self.versions
    def verifyVersion(self, version):
        pattern = re.compile("^" + version.replace(" ", ".*"), flags=re.I|re.M)
        versionName = re.search(pattern, "\n".join(self.versions))

        try:
            versionName = versionName.group()
        except:
            print("invalid version name! select from the following: \n{}".format(self.versions))
            return self.verifyVersion(input("> "))
        
        return versionName

    # get regional pokedex from game name 
    # IMPORTANT this does not identify regional variants at present
    def getPokedexFromRegion(self, version) -> list[dict]:
        version = self.verifyVersion(version)
        # get the pokedex via versionGroup
        versionGroup = self.get(BASE_VERSIONS, version).json()["version_group"]
        pokedex = self.get(versionGroup["url"]).json()["pokedexes"]

        if len(pokedex) == 1:
            res = self.get(pokedex[0]["url"]).json()["pokemon_entries"]
        
        else:
            res = []
            for dex in pokedex:
                pokedex = self.get(dex["url"]).json()["pokemon_entries"]
                res.extend(pokedex)
            
        return res
    
    def getEvoLinesFromPokedex(self, pokedex):
        visited = set()
        evoLines = []
        for mon in pokedex:
            if mon["pokemon_species"]["name"] not in visited:
                evoLineChain = self.get(self.get(mon["pokemon_species"]["url"]) 
                                    .json()["evolution_chain"]["url"]).json()["chain"]
                evoLine = self.recurseEvoLines(evoLineChain)
                visited.update(evoLine)
                evoLines.append(evoLine)
                
        return evoLines

    def recurseEvoLines(self, evoLineChain):
        monName = evoLineChain["species"]["name"]
        if evoLineChain["evolves_to"] == []:
            return [monName]
        else:
            res = []
            for evo in evoLineChain["evolves_to"]:
                if monName not in res: res.append(monName)
                res.extend(self.recurseEvoLines(evo))
            return res


if __name__ == "__main__":
    PokeapiAccess()