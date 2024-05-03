from bs4 import BeautifulSoup
import requests
import bigtree
from bigtree import Node, tree_to_dot, list_to_tree, find

# bs4 filtering criteria
def isEvoLine(tr):
    return len(tr.findAll("th")) == 0

# def isSplitLine(tr):
#     return

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
        tables = self.soup.findAll("table") #[:11]
        return tables
    
    # returns dict of trees for each evolutionary line
    def buildTree(self):
        res = {}

        for table in self.evoLinesSoup:
            # gets each family in a row
            # not sure how this interacts with split lines 
            # TODO CHECK AGAINST THE WEBSITE SOURCE

            # splitLine is the constant data between split evolution lines
            splitLine = []
            for row in table.findAll("tr"):
                # if the row is not an evolutionary line, reset splitLine and skip it
                if not isEvoLine(row):
                    splitLine = []
                    continue
                                
                line = self.buildLine(row, splitLine)
                res[find(line, lambda node: node.is_root).name] = line
                                
                # if the row is an evolutionary line and splitLine has not been assigned, assign it
                if splitLine == []:
                    splitLine = row.findAll("td", rowspan=True)
                
        return res
    
    def buildLine(self, data, splitLine):
        # each td is each cell in the row 
        dataCells = data.findAll("td")
        allCells = splitLine + dataCells

        # keep only the cells that don't have images (every third cell contains an image)
        relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-1) % 3 == 0]
        # keep only the relevant text
        evoText = [cell.text.strip() for cell in relevantCells]
        # write the node
        line = list_to_tree(["/".join(evoText)])

        return line

if __name__ == "__main__":
    scrapeEvoLines()