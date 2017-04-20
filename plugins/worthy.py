#!/usr/bin/env python

import re

from plugin_base import GladosPluginBase

MATCHING_RE = re.compile(r'(\bbolas\b)|(\bnicky b)', flags=re.I)
WORTHY_TEXT = 'May his return come quickly, and may we be found worthy'


class MHRCQAMWBFW(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return MATCHING_RE.search(msg['text']) is not None

    def handle_message(self, msg):
        self.send(WORTHY_TEXT, msg['channel'])

    @property
    def help_text(self):
        return WORTHY_TEXT
