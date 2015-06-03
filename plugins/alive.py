#!/usr/bin/env python

import re

from plugin_base import GladosPluginBase


class IAmAlive(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.match(r'^glados.*alive', msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        self.send('I am still alive', msg['channel'])
