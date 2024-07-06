class Pokemon:
    def __init__(self) -> None:
        self.name = ""
        self.gender = ""    # "(M)", "(F)", or ""
        self.item = ""      # "@ Sitrus Berry" or ""
        self.IVs = []       # [0 HP, 0 Atk...]
        self.ability = ""
        self.level = -1
        self.nature = ""
        self.moves = []

        self.trainer = ""

    def showdownExport(self):
        res = " ".join("{} ({}) {} {}".format(self.trainer, self.name, self.gender, self.item).split()) + "\n"
        res += "IVs: " + " / ".join(self.IVs) + "\n"
        res += "Ability: {}".format(self.ability) + "\n"
        res += "Level: {}".format(self.level) + "\n"
        if self.nature != "": res += "{} Nature".format(self.nature) + "\n"
        for move in self.moves: res += "- {}".format(move) + "\n"

        return res
    
    def __repr__(self):
        return self.showdownExport()