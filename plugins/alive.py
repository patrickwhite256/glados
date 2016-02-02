#!/usr/bin/env python

import re
import subprocess

from plugin_base import GladosPluginBase


class IAmAlive(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None
        return re.match(r'^glados.*alive', msg['text'], flags=re.I) is not None

    def handle_message(self, msg):
        message = 'I, GLaDOS @ {} ({}), am still alive.'.format(
            self.get_version(),
            'debug' if self.debug else 'production'
        )

        self.send(message, msg['channel'])

    def get_version(self):
        if not hasattr(self, 'version'):
            version = subprocess.check_output(
                ['git', 'rev-parse', 'HEAD']
            ).decode('utf8').replace('\n', '')
            setattr(self, 'version', version)
        return self.version
