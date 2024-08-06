import requests_cache
import json

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

    


if __name__ == "__main__":
    PokeapiAccess()