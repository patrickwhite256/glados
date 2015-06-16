#!/usr/bin/env python

import re

import requests

from plugin_base import GladosPluginBase

search_re = re.compile(r'glados,? urban me (.+)', re.I)
urban_api_templ = 'http://api.urbandictionary.com/v0/define?term={}'


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
        return search_re.search(msg['text'])

    def handle_message(self, msg):
        search_match = search_re.search(msg['text'])
        search_query = search_match.group(1)
        response = requests.get(urban_api_templ.format(search_query)).json()
        if response['list']:
            message_text = ''
            result = response['list'][0]
            definition = result['definition']
            attachments = [
                {
                    'fallback': definition,
                    'title': result['word'],
                    'title_link': result['permalink'],
                    'text': '{}\n{}'.format(definition, italicize(result['example'])),
                    'fields': [
                        {
                            'title': 'Author',
                            'value': result['author'],
                            'short': True
                        },
                        {
                            'title': 'Votes',
                            'value': '+{} -{}'.format(result['thumbs_up'], result['thumbs_down']),
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
