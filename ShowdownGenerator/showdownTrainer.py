class Trainer:
    def __init__(self, name="") -> None:
        self.name = name
        self.items = ""
        self.pokemon = []

    def export(self):
        for pokemon in self.pokemon: print(pokemon)

    def __repr__(self) -> str:
        self.export()