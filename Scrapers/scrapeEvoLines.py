from bs4 import BeautifulSoup
import requests
from bigtree import Node, tree_to_dot, list_to_tree, find

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


        self.evoLines = set()
        self.buildTree()

        for line in self.evoLines: line.hshow()

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
        # TODO unown
        # TODO check for rowspan s.t. slowpoke is correct
        # res = set()

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
                    # line = self.buildLine(row, tempTree)
                    # self.evoLines.add(line)

                i += 1

        return self.evoLines
    

    # first: get splitline data
    # make string list of splitline data
    # make string list of each subsequent line that's part of the split evolution
    # once you hit the end of the line, compile all

    def buildLine(self, data):
        if type(data) != list: data = [data]
        tree = list_to_tree(data)
        self.evoLines.add(tree)
        tree.hshow()
        return 
    
    def buildTempTree(self, data, isFirstEntry, j=1):
        if isFirstEntry: allCells = data.findAll("td", rowspan=True)
        else: allCells = data.findAll("td")

        # keep only the cells that don't have images (every third cell contains an image)
        relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-j) % 3 == 0]
        # keep only the relevant text
        evoText = [cell.text.strip() for cell in relevantCells]

        return "/".join(evoText)

    # def buildLine(self, data, splitLine):
    #     # each td is each cell in the row 
    #     dataCells = data.findAll("td")
    #     allCells = splitLine + dataCells

    #     # keep only the cells that don't have images (every third cell contains an image)
    #     relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-1) % 3 == 0]
    #     # keep only the relevant text
    #     evoText = [cell.text.strip() for cell in relevantCells]
    #     # write the node
    #     line = list_to_tree(["/".join(evoText)])

    #     return line

if __name__ == "__main__":
    scrapeEvoLines()