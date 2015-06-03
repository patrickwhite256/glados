#!/usr/bin/env python

import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import GladosPluginBase

memory_re = re.compile(r'glados,? know that ((?:(?!\sis).)+)\sis\s(.+)', re.I)
recall_re = re.compile(r'glados,? what is (.+)', re.I)


class WhatIs(GladosPluginBase):
    consumes_message = True

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return memory_re.search(msg['text']) or recall_re.search(msg['text'])

    def handle_message(self, msg):
        memory_match = memory_re.search(msg['text'])
        recall_match = recall_re.search(msg['text'])
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
            item = self.db_session.query(Item).filter_by(name=recall_match.group(1)).first()
            msg = {
                'id': 4,
                'type': 'message',
                'channel': msg['channel']
            }
            if item is None:
                message_text = '{0} is {0}'.format(recall_match.group(1))
            else:
                message_text = '{} is {}'.format(item.name, item.alias)
            self.send(message_text, msg['channel'])


class Item(Base):
    __tablename__ = 'items'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    alias = sqlalchemy.Column(sqlalchemy.String)
