import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import GladosPluginBase

create_re = re.compile(r'glados(?:,)? create group (\w+)', re.I)
delete_re = re.compile(r'glados(?:,)? create group (\w+)', re.I)
add_re = re.compile(r'glados(?:,)? add (\w+) to group (\w+)', re.I)
remove_re = re.compile(r'glados(?:,)? remove (\w+) from group (\w+)', re.I)
help_re = re.compile(r'glados(?:,)? help groups', re.I)
list_re = re.compile(r'glados(?:,)? list groups', re.I)
info_re = re.compile(r'glados(?:,)? show group (\w+)', re.I)
notify_re = re.compile(r'.*@(\w+)')


class Groups(GladosPluginBase):
    consumes_message = False

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        handled_exps = [
            create_re,
            delete_re,
            add_re,
            remove_re,
            help_re,
            list_re,
            info_re,
            notify_re
        ]
        for exp in handled_exps:
            if exp.match(msg['text']):
                return True
        return False

    def create_group(self, group, user):
        pass

    def delete_group(self, group, user):
        pass

    def add_to_group(self, name, group, user):
        pass

    def remove_from_group(self, name, group, user):
        pass

    def help_groups(self, user):
        pass

    def list_groups(self, user):
        pass

    def group_info(self, group, user):
        pass

    def notify_group(self, group, user):
        pass

    def handle_message(self, msg):
        handler_mapping = [
            (create_re, self.create_group),
            (delete_re, self.delete_group),
            (add_re, self.add_to_group),
            (remove_re, self.remove_from_group),
            (help_re, self.help_groups),
            (list_re, self.list_groups),
            (info_re, self.group_info),
            (notify_re, self.notify_group)
        ]
        for exp, handler in handler_mapping:
            match = exp.match(msg['text'])
            if match:
                handler(*exp.groups(), user=msg['user'])
                return
