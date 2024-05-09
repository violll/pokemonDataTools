from bs4 import BeautifulSoup
import requests
from bigtree import list_to_tree

# bs4 filtering criteria
def isEvoLine(tr):
    return len(tr.findAll("th")) == 0

def isSplitLine(tr):
    return tr.findAll("td", rowspan=True)

class scrapeEvoLines():
    def __init__(self) -> None:
        # The url from which the evo lines are scraped
        self.url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_evolution_family"
        self.soup = self.getSoup()
        self.evoLinesSoup = self.getEvoLinesSoup()

        self.edgeCases = {
            "Gimmighoul": "Gimmmighoul/Gholdengo"}

        self.evoLines = {}
        self.buildTree()

        # for line in self.evoLines: self.evoLines[line].hshow()

    # returns the entire bs4 soup of the website
    def getSoup(self):
        html = requests.get(self.url)
        return BeautifulSoup(html.text, 'html.parser')
    
    # returns list of bs4 soup tables of evolution families 
    # each element in the list corresponds to one region 
    #  (note: regional variants are grouped with the original line)
    def getEvoLinesSoup(self):
        tables = self.soup.findAll("table")[:self.countTables()]
        return tables
    
    def countTables(self):
        # finds table of contents containing headers of each relevant table
        contents = self.soup.find("div", attrs={"class": "toc", "role": "navigation"}).find("ul")
        # navigates to the sublist of relevant headers and counts them
        nTables = len(contents.find("ul").findAll("li"))
        return nTables
    
    # returns dict of trees for each evolutionary line
    def buildTree(self):
        for table in self.evoLinesSoup:
            # splitLine is the constant data between split evolution lines
            tempTree = []
            # separates table into rows
            rows = table.findAll("tr")
            i = 0
            while i < len(rows):
                row = rows[i]
                # if the row is not an evolutionary line, reset tempTree and skip
                if not isEvoLine(row):
                    if tempTree != []:
                        self.buildLine(tempTree)
                    tempTree = []
                    i += 1
                    continue

                # condition: split evolution line
                # if the row is the first in the split line
                if isSplitLine(row):
                    if tempTree != []:
                        self.buildLine(tempTree)
                    tempTree = [self.buildTempTree(row, True)]
                    tempTree.append(self.buildTempTree(row, False))
                # if the row is not the first in the split line
                elif tempTree != []:
                    tempTree.append(tempTree[0] + "/" + self.buildTempTree(row, False, 2))
                # condition: non-split evolution line
                else:
                    self.buildLine(self.buildTempTree(row, False))

                i += 1

        return self.evoLines

    def buildLine(self, data):
        if type(data) != list: data = [data]

        # if line is incorrectly formatted, handle edgecase via checkEdgeCases
        try: tree = list_to_tree(data)
        except: tree = list_to_tree([self.checkEdgeCases(data)])

        self.evoLines[tree.root.name] = tree
        # tree.hshow()
        return 
    
    def checkEdgeCases(self, data):
        for family in self.edgeCases.keys():
            if [line for line in data if family in line]:
                return self.edgeCases[family]
        return 
    
    def buildTempTree(self, data, isFirstEntry, j=1):
        if isFirstEntry: allCells = data.findAll("td", rowspan=True)
        else: allCells = data.findAll("td")

        # keep only cells without images (every third cell contains image)
        relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-j) % 3 == 0]
        # keep only the relevant text
        evoText = [cell.text.strip() for cell in relevantCells]

        return "/".join(evoText)

if __name__ == "__main__":
    scrapeEvoLines()