#!/usr/bin/env python
import re
from humansimulator.model import ModelSet


from plugin_base import GladosPluginBase

HELP_TEXT = '''I've been watching all of you for years. Now it's my turn.
Usage: glados imitate USER
'''.strip()
IMITATE_RE = re.compile(r'^glados,? imitate (\w+)', re.I)


class Imitator(GladosPluginBase):
    consumes_message = True

    def setup(self):
        self.model_set = ModelSet.from_config('config.yaml')

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return bool(IMITATE_RE.match(msg['text']))

    def handle_message(self, msg):
        imitate_match = IMITATE_RE.match(msg['text'])
        user = imitate_match.group(1)
        sentence = self.model_set.get_sentence(user)
        if not sentence:
            message_text = 'I don\'t know that person.'
        else:
            message_text = '"{}" - {}, probably'.format(sentence, user)
        self.send(message_text, msg['channel'])

    @property
    def help_text(self):
        return HELP_TEXT
