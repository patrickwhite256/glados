#!/usr/bin/evn python
from collections import defaultdict
import random

from drafto import player


class Bot(player.Player):
    def __init__(self, *args):
        super().__init__(*args)
        self.data = {}
        self.name = ''

    def pick(self):
        select_idx = self.select(self.current_pack)
        self.picks.append(self.current_pack.cards.pop(select_idx))
        self.on_pick()

    def notify(self):
        self.current_pack = self.pack_q.pop(0)
        self.pick()

    def select(self, pack):
        '''
            Should return the index of the card it wants from the pack
        '''
        raise NotImplementedError


class Moneybags(Bot):
    preferences = ['mythic', 'rare', 'uncommon', 'common', 'land']

    def select(self, pack):
        rarities = defaultdict(list)
        for i, card in enumerate(pack.cards):
            rarities[card.rarity].append(i)

        for preference in Moneybags.preferences:
            if preference in rarities:
                return random.choice(rarities[preference])
