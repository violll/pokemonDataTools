import requests
from bs4 import BeautifulSoup
import pandas as pd
import io
import json
from tqdm import tqdm

BASEURL = "https://pokemondb.net" 
DIV_IDS = {
    "x-y": "tab-moves-13",
    "omega-ruby-alpha-sapphire": "tab-moves-14"
}


def scrape_learnsets(game, output_path=r"C:\Users\Gil\OneDrive\Documents\Programming\pokemonDataTools\src\utils\test.json"):
    # get links for all pokemon 
    url = f"{BASEURL}/pokedex/game/{game}"

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"})
    soup = BeautifulSoup(r.content, features="lxml")

    divs = soup.find_all("div", attrs={"class": "infocard-list infocard-list-pkmn-lg"})
    all_links = set()
    for div in divs:
        dex = div.find_all("a", attrs={"class": "ent-name"})
        all_links = all_links | set([entry["href"] for entry in dex])
    
    # get learnsets for all pokemon
    res = {}

    for link in tqdm(all_links):
        url = f"{BASEURL}{link}/moves/6"
        name = link.split("/")[-1]
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0"})
        soup = BeautifulSoup(r.content, features="lxml")
        table = soup.find("div", attrs={"id": DIV_IDS[game]}).find("table")

        df = pd.read_html(io.StringIO(str(table)))[0]
        learnset = df.loc[:, ["Lv.", "Move"]].set_index("Lv.").rename(columns={"Move": name})
        learnset.Name = name
        res = res | learnset.to_dict()

    with open(output_path, "w+") as f:
        json.dump(res, f)