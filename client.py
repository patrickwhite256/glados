#!/usr/bin/env python

import json
import re
from importlib import import_module

import requests
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ws4py.client.threadedclient import WebSocketClient

SLACK_TOKEN = 'xoxb-5066460429-rINCEJaI40B297uZA2kVCs8L'
SLACK_RTM_START_URL = 'https://slack.com/api/rtm.start?token={}'.format(SLACK_TOKEN)
PLUGIN_FILENAME = 'plugins.json'

class GladosClient(WebSocketClient):
    def __init__(self, **kwargs):
        wsdata = requests.get(SLACK_RTM_START_URL).json()
        url = wsdata['url']
        self.plugin_classes = []
        self.plugins = []
        self.load_plugins()
        self.init_memory()
        self.init_plugins()
        return super().__init__(url, **kwargs)

    def opened(self):
        print('Hello!')

    def received_message(self, m):
        print(m)
        msg = json.loads(str(m))
        if 'ok' in msg:
            return
        if msg['type'] == 'message' and 'message' not in msg:
            self.handle_message(msg['text'], msg['channel'])

    def closed(self, code, reason=None):
        self.session.commit()
        print('You monster')

    def handle_message(self, text, channel):
        if re.match(r'^glados.*alive', text, flags=re.I):
            msg = {
                'id':1,
                'type':'message',
                'text':'I am still alive',
                'channel':channel
            }
            self.send(json.dumps(msg))
        if re.match(r'This[^\w]+sentence[^\w]+is[^\w+]false', text, re.I):
            msg = {
                'id':2,
                'type':'message',
                'text':'You monster',
                'channel':channel
            }
            self.send(json.dumps(msg))
            raise Exception
        match = re.match(r'^glados,? know that ((?:(?!\sis).)+)\sis\s(.+)', text, re.I)
        if match:
            name = match.group(1)
            alias = match.group(2)
            msg = {
                'id':3,
                'type':'message',
                'text':'I will remember that {} is {}'.format(name, alias),
                'channel':channel
            }
            self.send(json.dumps(msg))
            item = Item(name=name, alias=alias)
            self.session.add(item)
        match = re.match(r'glados,? what is (.+)', text, re.I)
        if match:
            item = self.session.query(Item).filter_by(name=match.group(1)).first()
            print(item)
            if item is None:
                return
            msg = {
                'id':4,
                'type':'message',
                'text':'{} is {}'.format(item.name, item.alias),
                'channel':channel
            }
            self.send(json.dumps(msg))

    def init_memory(self):
        engine = sqlalchemy.create_engine('sqlite:///memory.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)
        self.session = Session()
    
    def load_plugins(self):
        try:
            with open(PLUGINS_FILENAME) as plugins_file:
                plugins_dict = json.loads(plugins_file.read())
        except FileNotFoundError:
            print('Could not load plugins: file not found.')
            return
        except ValueError as e:
            print('Could not load plugins: malformed JSON:\n{0}'.format(e.args[0]))
        for module_name, class_dict in plugins_dict:
            try:
                plugin_class = import_module(class_dict['plugin_class'])
                for class_name in class_dict['deps']:
                    klass = getattr(module_name, class_name)
                self.plugin_classes.append(plugin_class)
            except ImportError as e:
                print('Problem loading plugin {}:\n{}'.format(class_dict['plugin_class'], e))

    def init_plugins(self):
        for plugin_class in self.plugin_classes:
            try:
                plugins.append(plugin_class(self.session, self.send))
            except Exception as e:
                print('Problem initializing plugin {}:\n{}'.format(plugin_class.__name__, e))



Base = declarative_base()


class Item(Base):
    __tablename__ = 'items'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    alias = sqlalchemy.Column(sqlalchemy.String)


# For debugging
if __name__ == '__main__':
    try:
        ws = GladosClient()
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
