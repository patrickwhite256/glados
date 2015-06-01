#!/usr/bin/env python

import json
import re

from plugin_base import GladosPluginBase


class IAmAlive(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.match(r'^glados.*alive', msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        out_msg = {
            'id': 1,
            'type': 'message',
            'text': 'I am still alive',
            'channel': msg['channel']
        }
        self.send(json.dumps(out_msg))
