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
BASE_LOCATION_ENCOUNTERS = "https://pokeapi.co/api/v2/location-area/{id or name}-area/"

class PokeapiAccess():
    def __init__(self) -> None:
        # initialize the session
        self.Session = requests_cache.CachedSession()
        self.placeholder = "{id or name}"   # placeholder to substitute data for api calls in the base_ global variables

        self.versions = self.get_versions()  # list of valid game versions to call

    def get_region_from_version(self, version):
        version = self.verify_version(version)
        version_group = self.get(BASE_VERSIONS, version).json()["version_group"]
        regions = self.get(version_group["url"]).json()["regions"]

        return [r["name"] for r in regions]

    def get_location_area_encounters(self, route, version):
        version = self.verify_version(version)

        # get region from version
        regions = self.get_region_from_version(version)

        # loop through regions
        # for most games there should only be one but in the case there are
        # multiple (ex: gold) the loop checks each region
        for region in regions:
            # reformat route
            location_area = f"{region}-{route}".lower().replace(" ", "-")

            # make the request
            location_area_encounters_response = self.get(BASE_LOCATION_ENCOUNTERS, location_area)

            if location_area_encounters_response.ok:
                location_area_encounters = location_area_encounters_response.json()
                self.pprint(location_area_encounters)

        return None

    def get_versions(self):
        versions_response = self.get(BASE_VERSIONS + "?limit=none").json()
        res = [entry["name"] for entry in versions_response["results"]]
        while versions_response["next"]:
            versions_response = self.get(versions_response["next"]).json()
            res.extend([entry["name"] for entry in versions_response["results"]])
        return res
    
    def get(self, url, modifier=""):
        response = self.Session.get(url.replace(self.placeholder, modifier))
        return response
    
    def pprint(self, data):
        print(json.dumps(data, indent=4))

    # ensure version name is formatted correctly by checking against self.versions
    def verify_version(self, version):
        pattern = re.compile("^" + version.replace(" ", ".*"), flags=re.I|re.M)
        version_name = re.search(pattern, "\n".join(self.versions))

        if version_name:
            version_name = version_name.group()
        else:
            print("invalid version name! select from the following: \n{}".format(self.versions))
            return self.verify_version(input("> "))
        
        return version_name

    # get regional pokedex from game name 
    # important this does not identify regional variants at present
    def get_pokedex_from_region(self, version) -> list[dict]:
        version = self.verify_version(version)
        # get the pokedex via version_group
        version_group = self.get(BASE_VERSIONS, version).json()["version_group"]
        pokedex = self.get(version_group["url"]).json()["pokedexes"]

        if len(pokedex) == 1:
            res = self.get(pokedex[0]["url"]).json()["pokemon_entries"]
        
        else:
            res = []
            for dex in pokedex:
                pokedex = self.get(dex["url"]).json()["pokemon_entries"]
                res.extend(pokedex)
            
        return res
    
    def get_evo_lines_from_pokedex(self, pokedex):
        visited = set()
        evo_lines = []
        for mon in pokedex:
            if mon["pokemon_species"]["name"] not in visited:
                evo_line_chain = self.get(self.get(mon["pokemon_species"]["url"]) 
                                    .json()["evolution_chain"]["url"]).json()["chain"]
                evo_line = self.recurse_evo_lines(evo_line_chain)
                visited.update(evo_line)
                evo_lines.append(evo_line)
                
        return evo_lines

    def recurse_evo_lines(self, evo_line_chain):
        mon_name = evo_line_chain["species"]["name"]
        if evo_line_chain["evolves_to"] == []:
            return [mon_name]
        else:
            res = []
            for evo in evo_line_chain["evolves_to"]:
                if mon_name not in res: 
                    res.append(mon_name)
                res.extend(self.recurse_evo_lines(evo))
            return res


if __name__ == "__main__":
    PokeAPI = PokeapiAccess()
    PokeAPI.get_location_area_encounters("Route 8", "X")