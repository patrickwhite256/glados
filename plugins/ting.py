#!/usr/bin/env python

import random
import re

from plugin_base import GladosPluginBase


class Ting(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.search(r'\bye+\b',
                         msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        response = 'ting'
        if random.random() < 10:
            response = 'haw'

        self.reply_to_message(msg, response)

    @property
    def help_text(self):
        return ':yeting:'
