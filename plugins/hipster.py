#!/usr/bin/env python

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
        self.send(hipster_text, msg['channel'])
