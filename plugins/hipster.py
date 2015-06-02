#!/usr/bin/env python

import json
import re

import requests

from plugin_base import GladosPluginBase


class BeHipster(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.match(r'^glados.*hipster', msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        hipster_json = requests.get('http://hipsterjesus.com/api/?paras=1&type=hipster-cetric').json()
        hipster_text = hipster_json['text'].split('.')[0].split('<p>')[1] + '.'
        out_msg = {
            'id': 1,
            'type': 'message',
            'text': hipster_text,
            'channel': msg['channel']
        }
        self.send(json.dumps(out_msg))
