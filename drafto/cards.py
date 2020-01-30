RARITY_ORDER = {
    'mythic': 0,
    'rare': 1,
    'uncommon': 2,
    'common': 3,
    'land': 4,
}

BASIC_TYPES = ['Plains', 'Island', 'Swamp', 'Mountain', 'Forest']

class Card(object):
    def __init__(self):
        self.name = ''
        self.rarity = ''
        self.image_url = ''
        self.colours = []
        self.foil = False

    def to_obj(self):
        return {
            'name': self.name,
            'rarity': self.rarity,
            'image_url': self.image_url,
            'colours': self.colours,
            'foil': self.foil,
        }

    @staticmethod
    def from_obj(self, obj):
        card = Card()
        card.name = obj['name']
        card.rarity = obj['rarity']
        card.image_url = obj['image_url']
        card.colours = obj['colours']
        card.foil = obj['foil']

    def __repr__(self):
        if self.foil:
            return '<SHINY {}:{}>'.format(self.rarity[0], self.name)
        return '<{}:{}>'.format(self.rarity[0], self.name)

    def __lt__(self, other):
        if RARITY_ORDER[self.rarity] < RARITY_ORDER[other.rarity]:
            return True
        if RARITY_ORDER[self.rarity] > RARITY_ORDER[other.rarity]:
            return False
        return self.name < other.name

    def __le__(self, other):
        if RARITY_ORDER[self.rarity] < RARITY_ORDER[other.rarity]:
            return True
        if RARITY_ORDER[self.rarity] > RARITY_ORDER[other.rarity]:
            return False
        return self.name <= other.name

    def __ge__(self, other):
        return not self < other

    def __gt__(self, other):
        return not self <= other


    def __eq__(self, other):
        return self.name == other.name



def from_scryfall(scryfall_obj):
    card = Card()

    card.name = scryfall_obj['name']
    card.rarity = scryfall_obj['rarity']
    card.image_url = scryfall_obj['image_uris']['normal']
    card.colours = scryfall_obj['colors']
    if card.name in BASIC_TYPES:
        card.rarity = 'land'

    return card
