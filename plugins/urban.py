#!/usr/bin/env python

import re

import requests

from plugin_base import GladosPluginBase

SEARCH_RE = re.compile(r'glados,? urban me (.+)', re.I)
URBAN_API_TPL = 'http://api.urbandictionary.com/v0/define?term={}'

HELP_TEXT = '''
A plugin that tells you what's what.
Usage: glados urban me PHRASE
'''.strip()


def italicize(string):
    lines = string.splitlines()
    return '\r\n'.join(['_' + l + '_' for l in lines])


class UrbanMe(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return SEARCH_RE.search(msg['text'])

    def handle_message(self, msg):
        search_match = SEARCH_RE.search(msg['text'])
        search_query = search_match.group(1)
        response = requests.get(URBAN_API_TPL.format(search_query)).json()
        if response['list']:
            message_text = ''
            result = response['list'][0]
            definition = result['definition']
            attachments = [
                {
                    'fallback': definition,
                    'title': result['word'],
                    'title_link': result['permalink'],
                    'text': '{}\n{}'.format(definition,
                                            italicize(result['example'])),
                    'fields': [
                        {
                            'title': 'Author',
                            'value': result['author'],
                            'short': True
                        },
                        {
                            'title': 'Votes',
                            'value': '+{} -{}'.format(result['thumbs_up'],
                                                      result['thumbs_down']),
                            'short': True
                        }
                    ],
                    'mrkdwn_in': ['text'],
                }
            ]
            self.send(message_text, msg['channel'], attachments)
        else:
            message_text = 'No results found for "{}"'.format(search_query)
            self.send(message_text, msg['channel'])

    @property
    def help_text(self):
        return HELP_TEXT
