#!/usr/bin/env python

import json
from importlib import import_module

import requests
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from ws4py.client.threadedclient import WebSocketClient

from plugin_base import DeclarativeBase as Base

SLACK_RTM_START_URL = 'https://slack.com/api/rtm.start?token={}'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'
PLUGINS_FILENAME = 'plugins.json'


class GladosClient(WebSocketClient):
    debug = False

    def __init__(self, slack_token, **kwargs):
        self.token = slack_token
        wsdata = requests.get(SLACK_RTM_START_URL.format(slack_token)).json()
        url = wsdata['url']
        self.plugin_classes = []
        self.plugins = []
        self.load_plugins()
        self.init_memory()
        self.init_plugins()
        return super().__init__(url, **kwargs)

    def opened(self):
        if self.debug:
            print('Hello!')

    def received_message(self, m):
        # TODO: ignore messages from bots to prevent loops
        if self.debug:
            print(m)
            # TODO: prevent debug runs from listening to any channel except the debug channel
        msg = json.loads(str(m))
        if 'ok' in msg:
            return
        for plugin in self.plugins:
            if plugin.can_handle_message(msg):
                plugin.handle_message(msg)
                if plugin.consumes_message:
                    return

    def closed(self, code, reason=None):
        self.session.commit()
        for plugin in self.plugins:
            plugin.teardown()
        if self.debug:
            print('You monster')

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
        for module_name, class_dict in plugins_dict.items():
            try:
                module = import_module('plugins.{}'.format(module_name))
                plugin_class = getattr(module, class_dict['plugin_class'])
                self.plugin_classes.append(plugin_class)
            except ImportError as e:
                print('Problem loading plugin {}:\n{}'.format(class_dict['plugin_class'], e))

    def init_plugins(self):
        for plugin_class in self.plugin_classes:
            try:
                self.plugins.append(plugin_class(self.session, self.postMessage))
            except Exception as e:
                print('Problem initializing plugin {}:\n{}'.format(plugin_class.__name__, e))
        for plugin in self.plugins:
            plugin.setup()

    def postMessage(self, message, channel, attachments=None):
        # TODO: add default channel
        data = {
            'token': self.token,
            'channel': channel,
            'text': message,
            'as_user': True
        }
        if attachments is not None:
            data['attachments'] = json.dumps(attachments)
        requests.post(SLACK_POST_MESSAGE_URL, data=data)


# For debugging
if __name__ == '__main__':
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
        ws = GladosClient(token)
        ws.debug = True
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
