#!usr/bin/env python

import re
import requests

from plugin_base import GladosPluginBase

GATHERER_IMG_TPL = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid={}&type=card'
CARD_NOT_FOUND_ERR_TPL = 'Whoops, looks like {} isn\'t a magic card'

# [[cardname]] fetches a card's image
cardimg_re = re.compile(r'.*?\[\[(.+?)\]\]')
# {{cardname}} gets detailed card info as text
oracle_re = re.compile(r'.*?{{(.+?)}}')


class CardFetcher(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return cardimg_re.match(msg['text']) or oracle_re.match(msg['text'])

    def handle_message(self, msg):
        cardimg_matches = cardimg_re.findall(msg['text'])
        oracle_matches = oracle_re.findall(msg['text'])

        for match in cardimg_matches:

            card_obj = get_card_obj(match)

            print(match)

            if not card_obj:
                print('Card not found')
                self.send(CARD_NOT_FOUND_ERR_TPL.format(match), msg['channel'])
                continue

            img_url = GATHERER_IMG_TPL.format(card_obj['id'])

            attachments = [{
                'fallback': card_obj['name'],
                'image_url': img_url
            }]

            self.send('', msg['channel'], attachments)

        for match in oracle_matches:

            card_obj = get_card_obj(match)

            if not card_obj:
                self.send(CARD_NOT_FOUND_ERR_TPL.format(match), msg['channel'])
                continue

            card_attachment = {
                'fallback': card_obj['name'],
                'title': card_obj['name'],
                'fields': [
                    {
                        'title': 'Mana Cost',
                        'value': card_obj['manaCost'],
                        'short': True
                    },
                    {
                        'title': 'Types',
                        'value': '{} - {}'.format(card_obj['type'], card_obj['subType']),
                        'short': True
                    },
                    {
                        'title': 'Text',
                        'value': card_obj['description'],
                        'short': False
                    }
                ]
            }

            if 'Creature' in card_obj['type']:
                card_attachment['fields'].append({
                    'title': 'P/T',
                    'value': '{}/{}'.format(card_obj['power'], card_obj['toughness']),
                    'short': True
                })
            if 'Planeswalker' in card_obj['type']:
                card_attachment['fields'].append({
                    'title': 'Loyalty',
                    'value': card_obj['loyalty'],
                    'short': True
                })

            attachments = [card_attachment]
            self.send('', msg['channel'], attachments)

'''
Query a web API for a card with the given name
Implementation subject to change as various MTG APIs are created and destroyed
Should always return a JSON in the mtgdb.info format:

*id                 Integer     : multiverse Id
relatedCardId       Integer     : multiverse Id of a related card, double faced and relying card
setNumber           Integer     : card number in the set
*name               String      : name of the card
searchName          String      : easy to search card name
*description        String      : the cards actions
flavor              String      : flavor text adds story, does not effect game
colors              String[]    : colors of card
*manaCost           String      : the description of mana to cast spell
convertedManaCost   Integer     : the amount of mana needed to cast spell
cardSetName         String      : the set or expansion the card belongs to
*type               String      : the type of card
*subType            String      : subtype of card
*power              Integer     : attack strength
*toughness          Integer     : defense strength
*loyalty            Integer     : loyalty points usually on planeswalkers
rarity              String      : the rarity of the card
artist              String      : artist of the illustrations
cardSetId           String      : the abbreviated name of the set
token               Boolean     : true if a token card, false if not
promo               Boolean     : true if a promo card, false if not
rulings             Ruling[]    : list of rulings for this card
formats             Format[]    : list of legal formats this card is in
releasedAt          Date        : when the card was released

* indicates properties that are currently in use and must be present in the returned json
'''


def get_card_obj(cardname):
    r = requests.get('http://api.mtgdb.info/cards/{}'.format(cardname))

    if (not r.json()) or (r.status_code is not requests.codes.ok):
        return None

    return r.json()[0]
