import bs4
import bigtree

class scrapeEvoLines():
    def __init__(self) -> None:
        # The url from which the evo lines are scraped
        self.url = "https://bulbapedia.bulbagarden.net/wiki/List_of_Pok%C3%A9mon_by_evolution_family"