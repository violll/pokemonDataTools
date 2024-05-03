from bs4 import BeautifulSoup
import requests
import bigtree

class scrapeEvoLines():
    def __init__(self) -> None:
        # The url from which the evo lines are scraped
        self.url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_evolution_family"
        self.soup = self.getSoup()
        self.evoLinesSoup = self.getEvoLinesSoup()

    # returns the entire bs4 soup of the website
    def getSoup(self):
        html = requests.get(self.url)
        return BeautifulSoup(html.text, 'html.parser')
    
    # returns list of bs4 soup tables of evolution families 
    # each element in the list corresponds to one region 
    #  (note: regional variants are grouped with the original line)
    def getEvoLinesSoup(self):
        tables = self.soup.findAll("table")
        return tables
    

if __name__ == "__main__":
    scrapeEvoLines()