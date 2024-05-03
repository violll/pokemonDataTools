from bs4 import BeautifulSoup
import requests
import bigtree

class scrapeEvoLines():
    def __init__(self) -> None:
        # The url from which the evo lines are scraped
        self.url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_evolution_family"
        self.soup = self.getSoup()

    def getSoup(self):
        html = requests.get(self.url)
        return BeautifulSoup(html.text, 'html.parser')
    

if __name__ == "__main__":
    scrapeEvoLines()