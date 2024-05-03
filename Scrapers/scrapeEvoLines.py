from bs4 import BeautifulSoup
import requests
import bigtree
from bigtree import Node, tree_to_dot, list_to_tree

class scrapeEvoLines():
    def __init__(self) -> None:
        # The url from which the evo lines are scraped
        self.url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_evolution_family"
        self.soup = self.getSoup()
        self.evoLinesSoup = self.getEvoLinesSoup()
        self.evoLines = self.buildTree()
        for line in self.evoLines.keys(): self.evoLines[line].hshow()

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
    
    # returns dict of trees for each evolutionary line
    def buildTree(self):
        """ how to set up a list of evolutionary lines and call/print them
        alolanR = Node("alolan ratatta")
        alolanRa = Node("alolan ratticate", parent=alolanR)
        rattata = Node("rattata")
        ratticate = Node("ratticate", parent=rattata)
        l = [alolanR, rattata]
        for x in l: x.hshow() 
        """

        res = {}

        for table in self.evoLinesSoup:
            rows = table.findAll("tr")
            for i in range(0, len(rows), 2):
                
                header = rows[i].text

                ## HIS CURRENTLY ONLY WORKS FOR FAMILIES WITHOUT MULTIPLE LINES 
                res[header] = self.buildLine(rows[i+1])
                
            return res
    
    def buildLine(self, data):
        ## THIS CURRENTLY ONLY WORKS FOR FAMILIES WITHOUT MULTIPLE LINES
        # each td is each cell in the row 
        allCells = data.findAll("td")
        # keep only the cells that don't have images (every third cell contains an image)
        relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-1) % 3 == 0]
        # keep only the relevant text
        evoText = [cell.text.strip() for cell in relevantCells]
        # write the node
        line = list_to_tree(["/".join(evoText)])

        # line.hshow()

        return line

if __name__ == "__main__":
    scrapeEvoLines()