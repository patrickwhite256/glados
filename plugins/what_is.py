#!/usr/bin/env python

import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import GladosPluginBase

MEMORY_RE = re.compile(r'glados,? know that ((?:(?!\sis).)+)\sis\s(.+)', re.I)
RECALL_RE = re.compile(r'glados,? what is (.+)', re.I)

HELP_TEXT = '''
A plugin that remembers what things are.
Usage:
glados, know that NAME is SOMETHING
glados, what is NAME
'''.strip()


class WhatIs(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return MEMORY_RE.search(msg['text']) or RECALL_RE.search(msg['text'])

    def handle_message(self, msg):
        memory_match = MEMORY_RE.search(msg['text'])
        recall_match = RECALL_RE.search(msg['text'])
        if memory_match:
            name = memory_match.group(1)
            alias = memory_match.group(2)
            item = self.db_session.query(Item).filter_by(name=name).first()
            if item is None:
                item = Item(name=name, alias=alias)
                self.db_session.add(item)
            else:
                item.alias = alias
            message_text = 'I will remember that {} is {}'.format(name, alias),
            self.send(message_text, msg['channel'])
        if recall_match:
            i_name = recall_match.group(1)
            item = self.db_session.query(Item).filter_by(name=i_name).first()
            msg = {
                'id': 4,
                'type': 'message',
                'channel': msg['channel']
            }
            if item is None:
                message_text = '{0} is {0}'.format(i_name)
            else:
                message_text = '{} is {}'.format(item.name, item.alias)
            self.send(message_text, msg['channel'])

    @property
    def help_text(self):
        return HELP_TEXT


class Item(Base):
    __tablename__ = 'items'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    alias = sqlalchemy.Column(sqlalchemy.String)
