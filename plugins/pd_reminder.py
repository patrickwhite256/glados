#!/usr/bin/env python

from plugin_base import TimedPluginBase


class PDReminder(TimedPluginBase):
    interval = '0 15 * * 0'
    help_text = 'Reminds you to do PD.'

    def can_handle_message(self, msg):
        return False

    def handle_message(self, msg):
        pass

    def run_timed_event(self):
        self.send('@channel: *Don\'t forget to do PD this week!*')
