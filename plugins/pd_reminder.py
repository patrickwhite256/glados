#!/usr/bin/env python

from plugin_base import GladosPluginBase


class PDReminder(GladosPluginBase):
    def handle_message(self, data):
        self.send('*Don\'t forget to do PD this week!*')
