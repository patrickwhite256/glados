#!/usr/bin/env python

from plugin_base import GladosPluginBase


class PDReminder(GladosPluginBase):
    def handle_message(self, data):
        self.send('@channel: *Don\'t forget to do PD this week!*')

    @property
    def help_text(self):
        return 'Reminds you to do PD.'
