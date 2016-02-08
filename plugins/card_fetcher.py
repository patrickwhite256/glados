#!usr/bin/env python

import re
import requests

from plugin_base import GladosPluginBase

GATHERER_IMG_TPL = 'http://gatherer.wizards.com/Handlers/Image.ashx?multiverseid={}&type=card'
CARD_NOT_FOUND_ERR_TPL = 'Whoops, looks like {} isn\'t a magic card'
MTGSTOCKS_LINK_TPL = '<{}|MTGStocks.com> price for {}'

# [[cardname]] fetches a card's image
cardimg_re = re.compile(r'.*?\[\[(.+?)\]\]')
# {{cardname}} gets detailed card info as text
oracle_re = re.compile(r'.*?{{(.+?)}}')
# $$cardname$$ fetches the price of the card
price_re = re.compile(r'.*?\$\$(.+?)\$\$')

HELP_TEXT = '''
[[cardname]] searches for card images
{{cardname}} searches for card oracle text
$$cardname$$ searches for card pricing information according to MTGStocks.com
'''

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
                        'value': format_mana(card_obj['manaCost']),
                        'short': True
                    },
                    {
                        'title': 'Types',
                        'value': '{} - {}'.format(card_obj['type'], card_obj['subType']),
                        'short': True
                    },
                    {
                        'title': 'Text',
                        'value': format_mana(card_obj['description']),
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

            card_obj = get_card_price(match)

            if not card_obj:
                self.send(CARD_NOT_FOUND_ERR_TPL.format(match), msg['channel'])
                continue

            prices = card_obj['prices']
            
            card_attachment = {
                'fallback': card_obj['name'],
                'title': card_obj['name'],
                'fields': [
                    {
                        'title': 'Set',
                        'value': card_obj['set'],
                        'short': True 
                    },
                    {
                        'title': 'Average',
                        'value': prices['avg'],
                        'short': True
                    }
                ]
            }

            if not card_obj['promo']:
                card_attachment['fields'].extend(
                    [
                        {
                            'title': 'Low',
                            'value': prices['low'],
                            'short': True
                        },
                        {
                            'title': 'High',
                            'value': prices['high'],
                            'short': True
                        }
                    ]
                )
                 
            
            attachments = [card_attachment] 
            self.send(MTGSTOCKS_LINK_TPL.format(card_obj['link'], match), msg['channel'], attachments, unfurl=False)

    @property
    def help_text(self):
        return HELP_TEXT


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

    query_url = 'https://api.deckbrew.com/mtg/cards?name={}'.format(cardname)
    r = requests.get(query_url)
    
    if (r.status_code != requests.codes.ok) or (not r.json()):
        return None

    api_json = next((card for card in r.json() if card['name'].lower() == cardname.lower()), None)

    if (api_json is None):
        if (len(r.json()) > 0):
            api_json = r.json()[0]
        else:
            return None

    formatted_json = {
        'id': api_json['editions'][0]['multiverse_id'],
        'name': api_json['name'],
        'description': api_json['text'],
        'manaCost': api_json['cost'],
        'type': (' ').join(api_json.get('types', [])).title(),
        'subType': (' ').join(api_json.get('subtypes', [])).title(),
        'power': api_json.get('power', ''),
        'toughness': api_json.get('toughness', ''),
        'loyalty': api_json.get('loyalty', '')
    }

    return formatted_json


def get_card_price(cardname):
    query_url = 'http://mtg-price-fetcher.us-west-1.elasticbeanstalk.com/cards/{}'.format(cardname)
    r = requests.get(query_url)
    
    if (r.status_code != requests.codes.ok) or (not r.json()):
        return None

    return r.json()


# replaces all manacost sequences (denoted by characters or numbers wrapped in {})
# with the appropriate manacost emoticons
def format_mana(string):
    return re.sub(r'\{(.+?)\}', format_mana_symbol, string)


def format_mana_symbol(match):
    sym = match.group(0).lower()
    sym = re.sub(r'[{}]', '', sym)

    if (len(sym) == 3 and sym[1] == '/'):
        sym = re.sub(r'\/', '', sym)

    if (len(sym) == 2 and sym[1] == 'p'):
        sym = sym[::-1]

    if (sym == 't'):
        return ':tap:'
    elif (sym == 'q'):
        return ':untap:'
    else:
        return ':{}mana:'.format(sym)
