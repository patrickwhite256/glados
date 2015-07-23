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
# $$cardname$$ fetches the price of the card
price_re = re.compile(r'.*?\$\$(.+?)\$\$')


class CardFetcher(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return cardimg_re.match(msg['text']) or oracle_re.match(msg['text']) or price_re.match(msg['text'])

    def handle_message(self, msg):
        cardimg_matches = cardimg_re.findall(msg['text'])
        oracle_matches = oracle_re.findall(msg['text'])
        pricing_matches = price_re.findall(msg['text'])

        for match in cardimg_matches:

            card_obj = get_card_obj(match)

            if not card_obj:
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

        for match in pricing_matches:

            price = get_card_price(match)

            self.send('CFB says the price of {} is {}'.format(match, price), msg['channel'], {})


'''
Query a web API for a card with the given name
Implementation subject to change as various MTG APIs are created and destroyed
Should always return a JSON in the mtgdb.info format:

*id                 Integer     : multiverse Id
*name               String      : name of the card
*description        String      : the cards actions
*manaCost           String      : the description of mana to cast spell
*type               String      : the type of card
*subType            String      : subtype of card
*power              Integer     : attack strength
*toughness          Integer     : defense strength
*loyalty            Integer     : loyalty points usually on planeswalkers


* indicates properties that are currently in use and must be present in the returned json
'''


def get_card_obj(cardname):

    queryUrl = 'https://api.deckbrew.com/mtg/cards?name={}'.format(cardname)
    r = requests.get(queryUrl)

    if (r.status_code is not requests.codes.ok) or (not r.json()):
        return None

    apiJson = r.json()[0]

    formattedJson = {
        'id': apiJson['editions'][0]['multiverse_id'],
        'name': apiJson['name'],
        'description': apiJson['text'],
        'manaCost': apiJson['cost'],
        'type': (' ').join(apiJson.get('types', [])).title(),
        'subType': (' ').join(apiJson.get('subtypes', [])).title(),
        'power': apiJson.get('power', ''),
        'toughness': apiJson.get('toughness', ''),
        'loyalty': apiJson.get('loyalty', '')
    }

    return formattedJson


def get_card_price(cardname):
    queryUrl = 'http://magictcgprices.appspot.com/api/cfb/price.json?cardname={}'.format(cardname)
    r = requests.get(queryUrl)

    print(queryUrl)

    if (r.status_code is not requests.codes.ok) or (not r.json()):
        return None

    print(r.json())

    return r.json()[0]
