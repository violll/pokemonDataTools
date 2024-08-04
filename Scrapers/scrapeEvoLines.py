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
            "Gimmighoul line": ["Gimmighoul", "Gholdengo"],
            "Unown": ["Unown"],
            "Rockruff line": ["Rockruff", "Lycanroc"]
            }

        self.evoLines = {}
        self.allMons = set()

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
    
    # counts the number of rows between evolution line headers
    def countRows(self, row):
        i = 0
        while True:
            rowToCheck = row.findNext("tr")
            if isEvoLine(rowToCheck): i += 1
            else: return i
            row = rowToCheck
    
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
                    family = row.find("th").text.replace("family", "").replace("*", "").strip()                    
                    
                    # if family name is in edgecases, add it here
                    if family in self.edgeCases.keys():
                        self.buildLine(self.edgeCases[family])
                        i += self.countRows(row) + 1
                        continue

                    # if tempTree is full, add the line and clear it 
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
                    tempTree.append(tempTree[0] + self.buildTempTree(row, False, 2))
                # condition: non-split evolution line
                else:
                    self.buildLine(self.buildTempTree(row, False))

                i += 1

        return self.evoLines

    def buildLine(self, lst):
        
        # convert line list to format that can be converted into tree        
        if type(lst[0]) == list: 
            data = ["/".join(line) for line in lst]
            monsToAdd = sum(lst, [])
        else: 
            data = ["/".join(lst)]
            monsToAdd = lst
        
        # convert into tree
        tree = list_to_tree(data)

        # if pokemon has not already been added to an evolutionary line, add it
        if tree.root.name not in self.allMons:
            self.evoLines[tree.root.name] = tree
            self.allMons.update(set(monsToAdd))
        # tree.hshow()
        return 
    
    def buildTempTree(self, data, isFirstEntry, j=1):
        if isFirstEntry: allCells = data.findAll("td", rowspan=True)
        else: allCells = data.findAll("td")

        # keep only cells without images (every third cell contains image)
        relevantCells = [allCells[i] for i in range(1, len(allCells)) if (i-j) % 3 == 0]
        # keep only the relevant text
        evoText = [cell.text.strip() for cell in relevantCells]

        return evoText

if __name__ == "__main__":
    scrapeEvoLines()