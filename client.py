#!/usr/bin/env python

import datetime
import json
import os
import re
import time
from importlib import import_module
from queue import Queue
from threading import Thread
from traceback import print_exc

import requests
import sqlalchemy
from croniter import croniter
from sqlalchemy.orm import sessionmaker
from ws4py.client.threadedclient import WebSocketClient

from plugin_base import DeclarativeBase as Base
from plugin_base import TimedPluginBase

SLACK_RTM_START_URL = 'https://slack.com/api/rtm.start?token={}'
SLACK_POST_MESSAGE_URL = 'https://slack.com/api/chat.postMessage'
SLACK_ADD_REACTION_URL = 'https://slack.com/api/reactions.add'
PLUGINS_FILENAME = 'plugins.json'

# TODO: move these to a configuration file
DEBUG_CHANNEL_NAME = 'aperture-science'
LOG_FILE_TEMPLATE = '/var/log/glados/{channel}/{date}.log'
DEBUG_LOG_FILE_TEMPLATE = '/tmp/glados/{channel}/{date}.log'
LOG_ENTRY_TEMPLATE = '[{time}] {name}: {message}'

PLUGIN_HELP_RE = re.compile(r'glados,? help (.*)', re.I)
HELP_RE = re.compile(r'glados,? help', re.I)

MSG_TYPE_TIMER = 1
MSG_TYPE_MESSAGE = 2
MSG_TYPE_CLOSED = 3
MSG_TYPE_TERMINATE = 4

HELP_TEXT = '''
Hello. I am GLaDOS (Genetic Lifeform and Disk Operating System).
I run a number of plugins for this slack.
Here are all the plugins I currently have installed:
{}
You can ask for help with a specific plugin by saying "glados help PLUGIN_NAME"

Contribute to my development at http://github.com/patrickwhite256/glados
'''.strip()


class GladosClient:
    def __init__(self, slack_token, debug=False):
        self.interval_thread = None
        self.socket_thread = None

        self.bot_users = []
        self.users = {}
        self.channels = {}
        self.debug_channel = None
        self.general_channel = None
        self.debug = debug
        self.token = slack_token

        date = datetime.date.today().strftime('%Y-%m-%d')
        wsdata = requests.get(SLACK_RTM_START_URL.format(slack_token)).json()
        self.slack_url = wsdata['url']
        for user in wsdata['users']:
            if user.get('is_bot'):
                self.bot_users.append(user['id'])
            self.users[user['id']] = user['name']
        self.bot_id = wsdata['self']['id']
        self.log_files = dict()
        for channel in wsdata['channels']:
            if channel['is_archived']:
                continue
            self.channels[channel['id']] = channel['name']
            if debug:
                log_file_name = DEBUG_LOG_FILE_TEMPLATE.format(
                    channel=channel['name'], date=date
                )
            else:
                log_file_name = LOG_FILE_TEMPLATE.format(
                    channel=channel['name'], date=date
                )
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
        self.timed_plugins = []
        self.load_plugins()
        self.init_memory()
        self.init_plugins()

    def run(self):
        queue = Queue()
        self.interval_thread = IntervalThread(queue)
        self.interval_thread.start()
        self.socket_thread = GladosWSClient(self.slack_url, queue, self.debug)
        self.socket_thread.start()
        while True:
            message = queue.get()
            if message['type'] == MSG_TYPE_TIMER:
                self.run_timed_plugins()
            elif message['type'] == MSG_TYPE_CLOSED:
                self.close()
            elif message['type'] == MSG_TYPE_MESSAGE:
                self.handle_message(message['msg'])

    def handle_message(self, message):
        msg = json.loads(message)
        if self.debug:
            print(message)
        msg_type = msg.get('type')
        if msg_type == 'message' and 'text' not in msg:
            # this is more trouble than it's worth handling, seriously
            return
        if 'channel' in msg and msg_type == 'message':
            self.log_message(msg['text'], msg['user'], msg['channel'])
        if (self.debug and msg.get('channel') != self.debug_channel) or \
           (not self.debug and msg.get('channel') == self.debug_channel):
            return
        if 'channel' in msg and \
           'message' not in msg and \
           msg_type == 'message' and \
           self.handle_help_message(msg['text'], msg['channel']):
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
            # pylint: disable=bare-except
            except:
                print_exc()
                # TODO: reload that plugin

    def close(self):
        self.session.commit()
        for plugin in self.plugins:
            plugin.teardown()
        for log_file in self.log_files.values():
            log_file.close()
        print('Stopping threads...')
        self.interval_thread.stop()
        self.interval_thread.join()
        if self.socket_thread.is_alive():
            self.socket_thread.stop()
            self.socket_thread.join()
        if self.debug:
            print('You monster')

    def init_memory(self):
        engine = sqlalchemy.create_engine('sqlite:///memory.db')
        Base.metadata.create_all(engine)
        session_cls = sessionmaker(engine)
        self.session = session_cls()

    def load_plugins(self):
        try:
            with open(PLUGINS_FILENAME) as plugins_file:
                plugins_dict = json.loads(plugins_file.read())
        except FileNotFoundError:
            print('Could not load plugins: file not found.')
            return
        except ValueError as e:
            print('Could not load plugins: malformed JSON:\n{0}'.format(
                e.args[0]
            ))
            return
        for module_name, class_dict in plugins_dict.items():
            try:
                module = import_module('plugins.{}'.format(module_name))
                self.plugin_metadata.append({
                    'name': class_dict['plugin_class'],
                    'class': getattr(module, class_dict['plugin_class'])
                })
            except ImportError as e:
                print('Problem loading plugin {}:\n{}'.format(
                    class_dict['plugin_class'], e
                ))

    def init_plugins(self):
        for plugin_data in self.plugin_metadata:
            plugin_class = plugin_data['class']
            try:
                # TODO: a more elegant way of passing data to plugins
                plugin = plugin_class(
                    self.session,
                    self.post_message,
                    react_to_message=self.react_to_message,
                    debug=self.debug,
                    users=self.users,
                    channels=self.channels
                )
                # make sure plugin has help text
                text = getattr(plugin, 'help_text')
                if not isinstance(text, str):
                    raise AttributeError('help_text must be a string')
                start_time = datetime.datetime.now()
                if isinstance(plugin, TimedPluginBase):
                    interval = getattr(plugin, 'interval')
                    if not isinstance(interval, str):
                        raise AttributeError('interval must be a string')
                    plugin.last_run_time = start_time
                    self.timed_plugins.append(plugin)
                self.plugins.append(plugin)
            # pylint: disable=broad-except
            except Exception as e:
                print('Problem initializing plugin {}:\n{}'.format(
                    plugin_class.__name__, e
                ))

        for plugin in self.plugins:
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

    def handle_help_message(self, message, channel):
        match = PLUGIN_HELP_RE.match(message)
        if match:
            plugin_name = match.group(1).lower()
            for plugin in self.plugins:
                if plugin.plugin_name.lower() == plugin_name:
                    self.post_message(plugin.help_text, channel)
                    return True
            self.post_message('No plugin of that name installed.', channel)
            return True
        if HELP_RE.match(message):
            plugin_list = '\n'.join([_.plugin_name for _ in self.plugins])
            help_text = HELP_TEXT.format(plugin_list)
            self.post_message(help_text, channel)
            return True
        return False

    def post_message(self, message, channel, attachments=None, as_user=True,
                     unfurl=True):
        data = {
            'token': self.token,
            'channel': channel,
            'text': message,
            'as_user': as_user,
            'link_names': 1,
            'unfurl_links': unfurl,
            'unfurl_media': unfurl
        }
        if attachments is not None:
            attachments_json = json.dumps(attachments)
            self.log_message(message + '|' + attachments[0]['fallback'],
                             self.bot_id, channel)
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

    def run_timed_plugins(self):
        now = datetime.datetime.now().replace(second=0, microsecond=0)

        for plugin in self.timed_plugins:
            time_iter = croniter(plugin.interval, plugin.last_run_time)
            next_time = time_iter.get_next(datetime.datetime).replace(
                second=0, microsecond=0)
            if next_time <= now:
                plugin.run_timed_event()
                plugin.last_run_time = now


class GladosWSClient(Thread):
    class WSClient(WebSocketClient):
        def __init__(self, slack_url, queue, debug):
            self.debug = debug
            self.queue = queue
            super().__init__(slack_url)
            self.running = True

        def opened(self):
            if self.debug:
                print('Hello!')

        def received_message(self, message):
            self.queue.put({'type': MSG_TYPE_MESSAGE, 'msg': str(message)})

        def closed(self, code, reason=None):
            if self.running:
                self.queue.put({'type': MSG_TYPE_CLOSED})

    def __init__(self, slack_url, queue, debug):
        self.client = self.WSClient(slack_url, queue, debug)
        super().__init__()

    def run(self):
        self.client.connect()
        self.client.run_forever()

    def stop(self):
        self.client.running = False
        self.client.close()


class IntervalThread(Thread):
    def __init__(self, queue):
        self.queue = queue
        self.running = True
        super().__init__()

    def run(self):
        count = 0
        while self.running:
            # sleeps in 1 second intervals so it can be stopped in a short time
            count += 1
            if count == 60:
                count = 0
                self.queue.put({'type': MSG_TYPE_TIMER})
            time.sleep(1)

    def stop(self):
        self.running = False


# For debugging
def main():
    try:
        token_file = open('.slack-token')
        token = token_file.read().strip()
        client = GladosClient(token, debug=True)
        client.run()
    except KeyboardInterrupt:
        client.close()

if __name__ == '__main__':
    main()
