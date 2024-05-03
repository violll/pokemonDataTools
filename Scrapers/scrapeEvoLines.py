from bs4 import BeautifulSoup
import requests
import bigtree
from bigtree import Node, tree_to_dot, list_to_tree, find

# bs4 filtering criteria
def notTableRowHeader(tr):
    return tr.name == "tr" and len(tr.findAll("th")) == 0

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
            # gets each family in a row
            # TODO not sure how this interacts with split lines 
            rows = [row for row in table.findNext() if notTableRowHeader(row)]

            for row in rows:
                ## CURRENTLY ONLY WORKS FOR FAMILIES WITHOUT SPLIT LINES 
                line = self.buildLine(row)
                res[find(line, lambda node: node.is_root).name] = line
                # print(find(line, lambda node: node.is_root).name)
                line.hshow()
                for x in res.keys(): res[x].hshow()
                continue
                # break
                
            return res
    
    def buildLine(self, data):
        ## THIS CURRENTLY ONLY WORKS FOR FAMILIES WITHOUT SPLIT LINES
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