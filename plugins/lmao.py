#!/usr/bin/env python

import re

from plugin_base import GladosPluginBase


class AyyLmao(GladosPluginBase):
    consumes_message = True

    REGEX_TO_REACTION = {
        r'\bay+(\b|lmao)': 'ayylmao',
        r'\btrigger(\b|ed)|\bPTSD': 'triggergif',
    }

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        for regex in self.REGEX_TO_REACTION:
            if re.search(regex, msg['text'], flags=re.I) is not None:
                return True
        return False

    def handle_message(self, msg):
        for regex, reaction in self.REGEX_TO_REACTION.items():
            if re.search(regex, msg['text'], flags=re.I) is not None:
                self.react_to_message(msg, reaction)

    @property
    def help_text(self):
        return ':ayylmao:'
