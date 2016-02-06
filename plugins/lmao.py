#!/usr/bin/env python

import re

from plugin_base import GladosPluginBase


class AyyLmao(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.search(r'\bay+(\b|lmao)',
                         msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        self.react_to_message(msg, 'ayylmao')

    @property
    def help_text(self):
        return ':ayylmao:'
