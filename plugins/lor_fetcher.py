#!usr/bin/env python

import base64
import binascii
import io
import json
import os
import re

from plugin_base import GladosPluginBase

LOR_DATA_PATH = 'lorcards'

NOT_FOUND_ERR_TPL = 'No match found for {}.'

CARD_RE = re.compile(r'.*?\[\[([^\]]+)\]\]')
DECK_RE = re.compile(r'.*?\{\{([^\}]+)\}\}')

LOR_DECKCODE_VERSION = 0x12
FACTIONS = {
    0: 'DE',
    1: 'FR',
    2: 'IO',
    3: 'NX',
    4: 'PZ',
    5: 'SI',
    6: 'BW',
    9: 'MT',
}

HELP_TEXT = '''
[[cardname]] searches for card name

extras (not yet implemented):
    o:"deal damage"
    o:challenger
    t:unit
    s:fast
    r:rare
    reg:demacia
    cmc=3
    pow=2
    tou=1

e.g.
[[t:champion pow=0 o:survive]]
'''


class LoRFetcher(GladosPluginBase):
    consumes_message = True

    def __init__(self, *args, **kwargs):
        self.channels = {}
        self.card_searcher = None
        self.channel = None
        self.debug_channel = None
        super().__init__(*args, **kwargs)

    def setup(self):
        for channel_id, channel_name in self.channels.items():
            if channel_name == 'aperture-science':
                self.debug_channel = channel_id
            if channel_name == 'leagueoflegends':
                self.channel = channel_id
        self.card_searcher = init_cardsearcher()

    def get_card(self, carddata):
        return self.card_searcher.get_card(carddata)

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None

        if msg.get('channel', 'D')[0] != 'D' and msg['channel'] != self.channel and msg['channel'] != self.debug_channel:
            return None

        return CARD_RE.match(msg['text']) or DECK_RE.match(msg['text'])

    def handle_message(self, msg):
        deck_match = DECK_RE.match(msg['text'])
        if deck_match:
            deck_code = deck_match.group(1)
            try:
                deck = decode_decklist(deck_code)
            except DecodeError as err:
                self.send('Could not decode decklist: {}'.format(err.msg), msg['channel'])
                return

            self.send('', msg['channel'], decklist_attachments(deck, self.card_searcher))

            return

        card_matches = CARD_RE.findall(msg['text'])

        for match in card_matches:
            cards = self.get_card(match)

            if not cards:
                self.send(NOT_FOUND_ERR_TPL.format(match), msg['channel'])
                continue

            fields = []
            if len(cards) > 1:
                fields.append({
                    'title': 'Associated Cards',
                    'value': ', '.join([card['name'] for card in cards[1:]]),
                })

            attachments = [({
                'title': cards[0]['name'],
                'fallback': cards[0]['name'],
                'image_url': cards[0]['assets'][0]['gameAbsolutePath'],
                'fields': fields,
                # 'blocks': cardblock(card),
            })]

            self.send('', msg['channel'], attachments)

    @property
    def help_text(self):
        return HELP_TEXT

USELESS_KEYWORDS = [
    'Burst',
    'Fast',
    'Skill',
    'Last Breath'
]


def filter_useless_keywords(keywords):
    useful_kwds = []
    for keyword in keywords:
        if keyword not in USELESS_KEYWORDS:
            useful_kwds.append(keyword)

    return useful_kwds


def cardblock(card):
    block = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': card['descriptionRaw'],
        }
    }

    typeline = {
        'type': 'plain_text',
        'text': card['type'],
    }
    pairs = []

    # type
    pairs.append(({
        'type': 'mrkdwn',
        'text': '*Type*',
    }, typeline))

    # cost
    pairs.append(({
        'type': 'mrkdwn',
        'text': '*Cost*',
    }, {
        'type': 'plain_text',
        'text': str(card['cost']),
    }))

    filtered_keywords = filter_useless_keywords(card['keywords'])
    if filtered_keywords:
        pairs.append(({
            'type': 'mrkdwn',
            'text': '*Keywords*',
        }, {
            'type': 'plain_text',
            'text': ', '.join(filtered_keywords),
        }))

    # region
    pairs.append(({
        'type': 'mrkdwn',
        'text': '*Region*',
    }, {
        'type': 'plain_text',
        'text': card['region'],
    }))

    if card['type'] == 'Unit':
        if card['supertype'] == 'Champion':
            typeline['text'] = 'Unit - Champion'
            if card['levelupDescriptionRaw']:
                block['text']['text'] = block['text']['text'] + '\n*Level Up*: ' + card['levelupDescriptionRaw']

        block['text']['text'] = block['text']['text'] + '\n\n{} / {}'.format(card['attack'], card['health'])

    if card['type'] == 'Spell':
        typeline['text'] = 'Spell - {}'.format(card['spellSpeed'])
        if card['supertype'] == 'Champion':
            typeline['text'] = 'Champion Spell - {}'.format(card['spellSpeed'])

    if len(pairs) % 2 == 1:
        pairs.append(({
            'type': 'mrkdwn',
            'text': ' ',
        }, {
            'type': 'mrkdwn',
            'text': ' ',
        }))

    fields = []
    for i in range(int(len(pairs) / 2)):
        fields.append(pairs[i*2][0])
        fields.append(pairs[i*2+1][0])
        fields.append(pairs[i*2][1])
        fields.append(pairs[i*2+1][1])

    block['fields'] = fields
    return block

LEVELED_RE = re.compile('(.+) (2|ii|l)$')


class CardSearcher:
    def __init__(self):
        self.cards_by_name = {}
        self.cards_by_id = {}
        for fname in os.listdir(LOR_DATA_PATH):
            with open(os.path.join(LOR_DATA_PATH, fname), encoding='utf-8') as data_file:
                all_cards = json.loads(data_file.read())
            for card in all_cards:
                self.add_card(card)

    def get_card(self, carddata):
        card = None
        cardname = carddata.lower()  # TODO: filters

        match = LEVELED_RE.match(cardname)
        if match:
            card = self.cards_by_name.get('{}_2'.format(match.group(1)))

        if not card:
            card = self.cards_by_name.get(cardname)
            if not card:
                return None
        cards = [card]

        refs = card['associatedCardRefs']
        for card_id in refs:
            card = self.cards_by_id[card_id]
            cards.append(card)
        return cards

    def get_card_by_id(self, card_id):
        return self.cards_by_id[card_id]

    def add_card(self, card):
        self.cards_by_id[card['cardCode']] = card
        if card['type'] == 'Unit' and card['supertype'] == 'Champion' and card['levelupDescriptionRaw'] == '':
            self.cards_by_name['{}_2'.format(card['name'].lower())] = card
            return
        self.cards_by_name[card['name'].lower()] = card


def init_cardsearcher():
    return CardSearcher()


class DecodeError(Exception):
    def __init__(self, msg):
        self.msg = msg


def read_varint(stream):
    res = 0
    while True:
        b = stream.read(1)
        if b == '':
            raise DecodeError('Unexpected EOF')
        b = ord(b)
        val = b & 0x7f
        res = (res << 7) + val
        if b & 0x80 == 0:
            break
    return res


def card_code(set_id, faction_id, card_n):
    try:
        faction_name = FACTIONS[faction_id]
    except KeyError:
        raise DecodeError('Unknown faction code')
    return '{:02}{}{:03}'.format(set_id, faction_name, card_n)


# returns a list of codes and values (e.g. ("01IO012", 3)) or throws DecodeError
def decode_decklist(deckstr):
    # manually pad
    deckstr += '=' * (8 - len(deckstr) % 8)
    try:
        b = base64.b32decode(deckstr)
    except binascii.Error:
        raise DecodeError('Error parsing base 32')
    stream = io.BytesIO(b)
    version_data = read_varint(stream)
    if version_data != LOR_DECKCODE_VERSION:
        raise DecodeError('Unknown version string')

    cards = []
    for card_count in range(3, 0, -1):
        n_sf = read_varint(stream)
        for _ in range(n_sf):
            n_cards = read_varint(stream)
            set_id = read_varint(stream)
            faction_id = read_varint(stream)
            for _ in range(n_cards):
                cards.append((card_code(set_id, faction_id, read_varint(stream)), card_count))

    return cards


def decklist_attachments(deck, searcher):
    parsed_cards = {'champion': [], 'Spell': [], 'Landmark': [], 'follower': []}
    for card_id, card_count in deck:
        card = searcher.get_card_by_id(card_id)
        card_txt = '[{}] {} x{}'.format(card['cost'], card['name'], card_count)
        if card['type'] == 'Unit':
            if card['supertype'] == 'Champion':
                parsed_cards['champion'].append(card_txt)
            else:
                parsed_cards['follower'].append(card_txt)
        else:
            parsed_cards[card['type']].append(card_txt)

    return [
        {
            'fallback': 'Runeterra Decklist',
            'blocks': [
                {
                    'type': 'section',
                    'fields': [
                        {
                            'type': 'mrkdwn',
                            'text': '*Champions*',
                        },
                        {
                            'type': 'mrkdwn',
                            'text': '*Spells*',
                        },
                        {
                            'type': 'plain_text',
                            'text': '\n'.join(sorted(parsed_cards['champion'])),
                        },
                        {
                            'type': 'plain_text',
                            'text': '\n'.join(sorted(parsed_cards['Spell'])),
                        },
                        {
                            'type': 'mrkdwn',
                            'text': '*Landmarks*',
                        },
                        {
                            'type': 'mrkdwn',
                            'text': '*Followers*',
                        },
                        {
                            'type': 'plain_text',
                            'text': '\n'.join(sorted(parsed_cards['Landmark'])),
                        },
                        {
                            'type': 'plain_text',
                            'text': '\n'.join(sorted(parsed_cards['follower'])),
                        },
                    ],
                }
            ],
        },
    ]
