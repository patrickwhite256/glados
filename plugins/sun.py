#!/usr/bin/env python

import re

from plugin_base import GladosPluginBase


class HereComesTheSun(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.search(r'\bsun(ny)?\b', msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        attachment_data = [{
            'fallback': 'Here comes the sun!',
            'text': '*Here comes the sun!*',
            'thumb_url': 'http://i.imgur.com/ERymiBz.png',
            'mrkdwn_in': ['text']
        }]
        self.send('', msg['channel'], attachment_data)
