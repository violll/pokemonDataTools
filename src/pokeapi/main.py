import json
import re
import sys
from pathlib import Path

import pandas as pd
import requests_cache

# adds the path absolutely
path = str(
    Path(Path(Path(__file__).parent.absolute()).parent.absolute()).parent.absolute()
)
sys.path.insert(0, path)

BASE_URL = "https://pokeapi.co/api/v2/"
BASE_POKEMON = "https://pokeapi.co/api/v2/pokemon/{id or name}/"
BASE_FORMS = "https://pokeapi.co/api/v2/pokemon-form/{id or name}/"
BASE_LOCATION = "https://pokeapi.co/api/v2/location/{id or name}/"
BASE_VERSIONS = "https://pokeapi.co/api/v2/version/{id or name}/"
BASE_VERSION_GROUPS = "https://pokeapi.co/api/v2/version-group/{id or name}"
BASE_SPECIES = "https://pokeapi.co/api/v2/pokemon-species/{id or name}/"
BASE_LOCATION_ENCOUNTERS = "https://pokeapi.co/api/v2/location-area/{id or name}/"

VALID_CONDITION_VALUES = {
    "kanto": {"separators": ["time-morning", "time-day", "time-night"], "applied_to_all": []},
    "johto": {
        "separators": ["time-morning", "time-day", "time-night"], 
        "applied_to_all": []},
    "hoenn": {"separators": [], "applied_to_all": []},
    "sinnoh": {
        "separators": ["time-morning", "time-day", "time-night"],
        "applied_to_all": ["swarm-no", None, "radar-off", "slot2-none"],
    },
    "unova": {
        "separators": ["season-spring", "season-summer", "season-autumn", "season-winter"], 
        "applied_to_all": []},
    "kalos": {"separators": [], "applied_to_all": []},
    "alola": {"separators": [], "applied_to_all": []}
}


def set_union(sets):
    return set().union(*sets)


class PokeapiAccess:
    def __init__(self) -> None:
        # initialize the session
        self.Session = requests_cache.CachedSession()
        self.placeholder = "{id or name}"  # placeholder to substitute data for api calls in the base_ global variables

        self.versions = self.get_versions()  # list of valid game versions to call

    def get_region_from_version(self, version):
        version = self.verify_version(version)
        version_group = self.get(BASE_VERSIONS, version).json()["version_group"]
        regions = self.get(version_group["url"]).json()["regions"]

        return [r["name"] for r in regions]

    def get_location_area_encounters(self, route, version, additional_ruleset_encounters=False):
        version = self.verify_version(version)

        # get region from version
        regions = self.get_region_from_version(version)

        # loop through regions
        # for most games there should only be one but in the case there are
        # multiple (ex: gold) the loop checks each region
        for region in regions:
            valid_condition_values = VALID_CONDITION_VALUES[region]

            # reformat route
            if re.search(r"(?<!-)route", route, flags=re.I):
                location_area = f"{region}-{route}-area".lower().replace(" ", "-")
            else:
                location_area = route

            # make the request
            location_area_encounters_response = self.get(
                BASE_LOCATION_ENCOUNTERS, location_area
            )

            if location_area_encounters_response.ok:
                encounters = []
                location_area_encounters = location_area_encounters_response.json()

                for pokemon in location_area_encounters["pokemon_encounters"]:
                    pokemon_name = pokemon["pokemon"]["name"]

                    # check if a special ruleset is being used
                    # if so, encounters will be passed into additional_ruleset_encounters
                    # only these encounters should be parsed
                    if (
                        additional_ruleset_encounters
                        and pokemon_name not in additional_ruleset_encounters
                    ):
                        continue

                    # loop through versions and select the correct one
                    for pokemon_version in pokemon["version_details"]:
                        if pokemon_version["version"]["name"] == version:
                            df = pd.DataFrame.from_dict(
                                pokemon_version["encounter_details"], orient="columns"
                            )
                            df["method"] = df["method"].apply(lambda x: x["name"])
                            df["pokemon"] = pokemon_name

                            # do something with condition values here
                            if df["condition_values"].apply(lambda x: len(x)).sum() > 0:
                                # separate each condition into its own row
                                df = df.explode("condition_values")

                                # extract the name of the condition value
                                df["condition_values"] = df["condition_values"].apply(
                                    lambda x: x["name"] if isinstance(x, dict) else None
                                )

                                # check if there are any valid condition values
                                if (
                                    len(
                                        set(df["condition_values"]).intersection(
                                            set(
                                                valid_condition_values["separators"]
                                                + valid_condition_values[
                                                    "applied_to_all"
                                                ]
                                            )
                                        )
                                    )
                                    > 0
                                ):
                                    # extract the valid condition values
                                    separators = df[
                                        df["condition_values"].isin(
                                            valid_condition_values["separators"]
                                        )
                                    ]
                                    applied_to_all = df[
                                        df["condition_values"].isin(
                                            valid_condition_values["applied_to_all"]
                                        )
                                    ]

                                    # modify the condition value to match each separator
                                    applying_to_all = []
                                    for i in range(
                                        len(valid_condition_values["separators"])
                                    ):
                                        applying_to_sep = applied_to_all.copy(deep=True)
                                        applying_to_sep["condition_values"] = (
                                            valid_condition_values["separators"][i]
                                        )
                                        applying_to_all.append(applying_to_sep)

                                    df = pd.concat([separators] + applying_to_all)

                                else:
                                    # if there are no valid conditions, the pokemon cannot be encountered
                                    continue
                            else:
                                df["condition_values"] = ""
                            encounters.append(df)
                            break
                
                # check to see if extraction was successful
                if len(encounters) > 0:
                    df = pd.concat(encounters)

                    # set the level range by the minimum and maximum level values
                    df["level_range"] = df.apply(
                        lambda x: set(range(x["min_level"], x["max_level"] + 1)), axis=1
                    )

                    # group by method and pokemon
                    df["subzone"] = ""
                    return df.groupby(by=["method", "subzone", "condition_values", "pokemon"]).agg(
                        chance=("chance", "sum"), level_range=("level_range", set_union)
                    )
                else: 
                    print(f"{version} - {region} - {route} has no valid encounters. Check your input. Does PokeAPI have this data?")
                    return None

        # check to see if the location-area is actually an location
        if re.search("route", route, flags=re.I):
            # loop to find the correct region
            for region in regions:
                location = self.get(BASE_LOCATION, f"{region}-{route}".lower().replace(" ", "-"))
                if location.ok: 
                    break
        else:
            location = self.get(BASE_LOCATION, route.lower().replace(" ", "-"))

        if location.ok:
            location_areas = location.json()["areas"]
            res = []
            for location_area in location_areas:
                location_area_encounters = self.get_location_area_encounters(location_area["name"], version, additional_ruleset_encounters)
                if isinstance(location_area_encounters, pd.DataFrame):
                    location_area_encounters.index = location_area_encounters.index.set_levels([location_area["name"]], level=1)
                    res.append(location_area_encounters)
            df = pd.concat(res)
            return df
        
        # if you make it down here, there's something wrong with your input
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
        pattern = re.compile("^" + version.replace(" ", ".*"), flags=re.I | re.M)
        version_name = re.search(pattern, "\n".join(self.versions))

        if version_name:
            version_name = version_name.group()
        else:
            print(
                "invalid version name! select from the following: \n{}".format(
                    self.versions
                )
            )
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
                evo_line_chain = self.get(
                    self.get(mon["pokemon_species"]["url"]).json()["evolution_chain"][
                        "url"
                    ]
                ).json()["chain"]
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
    print(PokeAPI.get_location_area_encounters("route 1", "sword"))
