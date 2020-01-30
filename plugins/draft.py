#!/usr/bin/env python

import random
import re

from plugin_base import GladosPluginBase
from drafto import drafto

HELP_TEXT = '''
:dab:
'''.strip()

create_re = re.compile(r'^glados(?:,)? create draft ((<@U[A-Z0-9]+>\s?)+)$', re.I)
stop_re   = re.compile(r'^glados(?:,)? stop draft', re.I)
pick_re   = re.compile(r'^pick (\d+)$', re.I)
status_re = re.compile(r'^glados status draft')


class Drafto(GladosPluginBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.draft = None
    consumes_message = False

    def setup(self):
        pass # TODO: load draft

    def teardown(self):
        pass # TODO: commit draft

    def can_handle_message(self, msg):
        if msg['type'] != 'message' or 'message' in msg:
            return None

        handled_exps = [
            create_re,
            stop_re,
            pick_re,
            status_re,
        ]

        for exp in handled_exps:
            if exp.match(msg['text']):
                return True
        return False

    def handle_message(self, msg):
        handler_mapping = [
            (create_re, self.start_draft),
            (stop_re, self.stop_draft),
            (pick_re, self.pick_card),
            (status_re, self.status),
        ]
        for exp, handler in handler_mapping:
            match = exp.match(msg['text'])
            if match:
                handler(
                    *match.groups(),
                    user=msg['user'],
                    channel=msg['channel']
                )
                return

    def start_draft(self, *args, user, channel):
        if self.draft:
            self.send(
                'Draft in progress. Cannot run concurrent drafts (yet).',
                channel
            )
            return

        user_ids = set(re.split(r'\s', args[0]))
        if len(user_ids) > 8:
            self.send(
                'Cannot start draft with more than eight humans.',
                channel
            )
            return

        message = 'Starting draft with {}'.format(' '.join(user_ids))
        self.send(message, channel)

        user_ids = [u[2:-1] for u in user_ids]

        def notify_func(user_id, message):
            self.send(message, user_id)

        def finish_func(msg):
            for user_id in user_ids:
                msg = re.sub(r'(\bU[A-Z0-9]+\b)', r'<@\1>', msg)
                self.send(msg, user_id)
            self.draft = None

        self.draft = drafto.Draft(['thb', 'thb', 'thb'], user_ids, notify_func, finish_func)
        self.send('Draft initialized', channel)

    def stop_draft(self, user, channel):
        if not self.draft:
            self.send(
                'No draft in progress.',
                channel
            )
            return

        self.draft = None
        self.send(
            'Stopped draft.',
            channel
        )

    def pick_card(self, card, user, channel):
        if channel[0] != 'D':  # ignore non-private messages
            return
        if not self.draft or not self.draft.humans_by_id[user]:
            self.send(
                'You are not participating in a draft.',
                channel
            )
            return

        # TODO: concurrency concerns lol
        try:
            self.draft.humans_by_id[user].pick(int(card) - 1)
        except Exception as ex:
            self.send(
                'Error picking card: {}'.format(str(ex)),
                channel
            )

    def status(self, user, channel):
        msg = 'There is no draft in progress.'
        if self.draft:
            msg = re.sub(r'(\bU[A-Z0-9]+\b)', r'<@\1>', self.draft.status())

        self.send(msg, channel)

    @property
    def help_text(self):
        return HELP_TEXT
