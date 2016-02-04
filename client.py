#!/usr/bin/env python

import datetime
import json
import os
from importlib import import_module
from traceback import print_exc

import requests
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from ws4py.client.threadedclient import WebSocketClient

from plugin_base import DeclarativeBase as Base

SLACK_RTM_START_URL = 'https://slack.com/api/rtm.start?token={}'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'
SLACK_ADD_REACTION_URL = 'https://slack.com/api/reactions.add'
PLUGINS_FILENAME = 'plugins.json'

# TODO: move these to a configuration file
DEBUG_CHANNEL_NAME = 'aperture-science'
LOG_FILE_TEMPLATE = '/var/log/glados/{channel}/{date}.log'
DEBUG_LOG_FILE_TEMPLATE = '/tmp/glados/{channel}/{date}.log'
LOG_ENTRY_TEMPLATE = '[{time}] {name}: {message}'


class GladosClient(WebSocketClient):
    def __init__(self, slack_token, debug=False, **kwargs):
        self.debug = False
        self.bot_users = []
        self.users = {}
        self.channels = {}
        self.debug_channel = None
        self.general_channel = None
        self.async_plugins = {}
        date = datetime.date.today().strftime('%Y-%m-%d')
        self.debug = debug
        self.token = slack_token
        wsdata = requests.get(SLACK_RTM_START_URL.format(slack_token)).json()
        url = wsdata['url']
        for user in wsdata['users']:
            if user['is_bot']:
                self.bot_users.append(user['id'])
            self.users[user['id']] = user['name']
        self.bot_id = wsdata['self']['id']
        self.log_files = dict()
        for channel in wsdata['channels']:
            if channel['is_archived']:
                continue
            self.channels[channel['id']] = channel['name']
            if debug:
                log_file_name = DEBUG_LOG_FILE_TEMPLATE.format(channel=channel['name'], date=date)
            else:
                log_file_name = LOG_FILE_TEMPLATE.format(channel=channel['name'], date=date)
            try:
                os.makedirs(os.path.dirname(log_file_name))
            except:
                pass
            log_file = open(log_file_name, 'a+')
            self.log_files[channel['id']] = log_file
            if channel['name'] == DEBUG_CHANNEL_NAME:
                self.debug_channel = channel['id']
            if channel['is_general']:
                self.general_channel = channel['id']
        if self.debug:
            self.general_channel = self.debug_channel

        self.plugin_metadata = []
        self.plugins = []
        self.load_plugins()
        self.init_memory()
        self.init_plugins()
        return super().__init__(url, **kwargs)

    def opened(self):
        if self.debug:
            print('Hello!')

    def received_message(self, m):
        msg = json.loads(str(m))
        if 'channel' in msg and 'message' not in msg and msg['type'] == 'message':
            self.log_message(msg['text'], msg['user'], msg['channel'])
        if self.debug:
            print(m)
            if 'channel' in msg and msg['channel'] != self.debug_channel:
                return
        else:
            if 'channel' in msg and msg['channel'] == self.debug_channel:
                return
        if 'user' in msg and msg['user'] in self.bot_users:
            return
        if 'ok' in msg:
            return
        for plugin in self.plugins:
            try:
                if plugin.can_handle_message(msg):
                    plugin.handle_message(msg)
                    if plugin.consumes_message:
                        return
            except:
                print_exc()
                # TODO: reload that plugin

    def closed(self, code, reason=None):
        self.session.commit()
        for plugin in self.plugins + list(self.async_plugins.values()):
            plugin.teardown()
        if self.debug:
            print('You monster')
        for log_file in self.log_files.values():
            log_file.close()

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
                self.plugin_metadata.append({
                    'name': class_dict['plugin_class'],
                    'class': getattr(module, class_dict['plugin_class']),
                    'type': class_dict['plugin_type']
                })
            except ImportError as e:
                print('Problem loading plugin {}:\n{}'.format(class_dict['plugin_class'], e))

    def init_plugins(self):
        for plugin_data in self.plugin_metadata:
            plugin_class = plugin_data['class']
            plugin_name = plugin_data['name']
            try:
                if plugin_data['type'] == 'normal':
                    # TODO: a more elegant way of passing data to plugins
                    self.plugins.append(plugin_class(
                        self.session,
                        self.post_message,
                        react_to_message=self.react_to_message,
                        debug=self.debug,
                        users=self.users,
                        channels=self.channels
                    ))
                elif plugin_data['type'] == 'async':
                    self.async_plugins[plugin_name] = plugin_class(
                        self.session,
                        self.post_general
                    )
            except Exception as e:
                print('Problem initializing plugin {}:\n{}'.format(plugin_class.__name__, e))
        for plugin in self.plugins + list(self.async_plugins.values()):
            plugin.setup()

    def log_message(self, message, user_id, channel_id):
        try:
            log_file = self.log_files[channel_id]
        except KeyError:
            return
        log_file.write(LOG_ENTRY_TEMPLATE.format(
            time=datetime.datetime.now().strftime('%H:%M:%S'),
            name=self.users[user_id],
            message=message + '\n'
        ))
        log_file.flush()

    def post_message(self, message, channel, attachments=None,
                     link_names=True, as_user=True):
        # TODO: add default channel
        data = {
            'token': self.token,
            'channel': channel,
            'text': message,
            'as_user': as_user
        }
        if link_names:
            data['link_names'] = 1
        if attachments is not None:
            attachments_json = json.dumps(attachments)
            self.log_message(message + '|' + attachments[0]['fallback'], self.bot_id, channel)
            data['attachments'] = attachments_json
        else:
            self.log_message(message, self.bot_id, channel)
        response = requests.post(SLACK_POST_MESSAGE_URL, data=data)
        if self.debug:
            print(response)

    def react_to_message(self, msg, reaction):
        data = {
            'token': self.token,
            'channel': msg['channel'],
            'timestamp': msg['ts'],
            'name': reaction
        }
        response = requests.post(SLACK_ADD_REACTION_URL, data=data)
        if self.debug:
            print(response)

    def post_general(self, message):
        self.post_message(message, self.general_channel)

    def handle_async(self, plugin, data):
        self.async_plugins[plugin].handle_message(data)


# For debugging
if __name__ == '__main__':
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
        ws = GladosClient(token, debug=True)
        ws.connect()
        ws.run_forever()
    except KeyboardInterrupt:
        ws.close()
