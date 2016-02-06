#!/usr/bin/env python

import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import GladosPluginBase

KARMA_RE = re.compile(r'karma ([A-Za-z_]+)', re.I)
ADD_RE = re.compile(r'([A-Za-z_]+)\+\+', re.I)
TAKE_RE = re.compile(r'([A-Za-z_]+)--', re.I)

HELP_TEXT = '''
A plugin for tracking karma.
Usage:
NAME++
NAME--
karma NAME
'''


class Karmator(GladosPluginBase):
    consumes_message = False

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return \
            KARMA_RE.match(msg['text']) or \
            ADD_RE.search(msg['text']) or \
            TAKE_RE.search(msg['text'])

    def handle_message(self, msg):
        karma_match = KARMA_RE.match(msg['text'])
        add_match = ADD_RE.search(msg['text'])
        take_match = TAKE_RE.search(msg['text'])
        if karma_match:
            name = karma_match.group(1).lower()
            item = self.db_session.query(KarmaItem).filter_by(
                name=name
            ).first()
            if item is None:
                plus = 0
                minus = 0
            else:
                plus = item.plus
                minus = item.minus
            self.send('{}: {} [{}++, {}--]'.format(name, plus - minus, plus,
                                                   minus), msg['channel'])
        elif add_match:
            name = add_match.group(1).lower()
            item = self.db_session.query(KarmaItem).filter_by(
                name=name
            ).first()
            if item is None:
                item = KarmaItem(name=name, plus=0, minus=0)
                self.db_session.add(item)
            item.plus += 1
        elif take_match:
            name = take_match.group(1).lower()
            item = self.db_session.query(KarmaItem).filter_by(
                name=name
            ).first()
            if item is None:
                item = KarmaItem(name=name, plus=0, minus=0)
                self.db_session.add(item)
            item.minus += 1

    @property
    def help_text(self):
        return HELP_TEXT


class KarmaItem(Base):
    __tablename__ = 'karmaitems'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    plus = sqlalchemy.Column(sqlalchemy.Integer)
    minus = sqlalchemy.Column(sqlalchemy.Integer)
