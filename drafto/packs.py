from collections import defaultdict
import copy
import random
import time

import requests

from drafto import cards


SCRYFALL_SEARCH_URL = 'https://api.scryfall.com/cards/search?order=set&q=e%3A{}+in%3Abooster&unique=cards'
SCRYFALL_BACKOFF_TS = 0.5

ALL_CARDS_CACHE = {}

class Pack(object):
    def __init__(self):
        self.cards = []

    def __repr__(self):
        return str(sorted(self.cards))



# TODO: special pack rules
# (DOM legends, RNA/GRN gates, etc)
def generate_pack(set_code):
    full_set = get_all_cards(set_code)
    while True:
        pack = Pack()

        is_mythic = (random.random() < 1.0/8.0)
        if is_mythic:
            pack.cards.append(random.choice(full_set['mythic']))
        else:
            pack.cards.append(random.choice(full_set['rare']))

        pack.cards.extend(random.sample(full_set['uncommon'], 3))

        is_foil = (random.random() < 1.0/3.0)

        if is_foil:
            pack.cards.extend(random.sample(full_set['common'], 9))
            all_cards = full_set['mythic'] + full_set['rare'] + full_set['uncommon'] + full_set['common'] + full_set['land']
            foil_card = copy.copy(random.choice(all_cards))
            foil_card.foil = True
            pack.cards.append(foil_card)
        else:
            pack.cards.extend(random.sample(full_set['common'], 10))

        pack.cards.append(random.choice(full_set['land']))

        colours_represented = set()
        for card in pack.cards:
            for colour in card.colours:
                colours_represented.add(colour)

        if len(colours_represented) != 5:
            continue

        return pack

# TODO cache results outside of locally
def get_all_cards(set_code):
    if ALL_CARDS_CACHE.get(set_code):
        return ALL_CARDS_CACHE[set_code]

    cards_by_rarity = defaultdict(list)
    page_url = SCRYFALL_SEARCH_URL.format(set_code)
    while True:
        res = requests.get(page_url)

        if res.status_code != requests.codes.ok or not res.json():
            raise Exception('bad response from scryfall')
        
        for card_data in res.json()['data']:
            card = cards.from_scryfall(card_data)
            cards_by_rarity[card.rarity].append(card)
        
        page_url = res.json().get('next_page')

        if not page_url:
            break

        time.sleep(SCRYFALL_BACKOFF_TS)

    ALL_CARDS_CACHE[set_code] = cards_by_rarity

    return cards_by_rarity
