from plugin_base import TimedPluginBase


class Annoying(TimedPluginBase):
    help_text = 'I\'M REALLY ANNOYING'
    interval = '* * * * *'

    def __init__(self, *args, **kwargs):
        self.channels = {}
        self.debug_channel = None
        super().__init__(*args, **kwargs)

    def setup(self):
        for channel_id, channel_name in self.channels.items():
            if channel_name == 'aperture-science':
                self.debug_channel = channel_id
                return

    def can_handle_message(self, msg):
        pass

    def handle_message(self, msg):
        pass

    def run_timed_event(self):
        self.send('Hi!', self.debug_channel)
