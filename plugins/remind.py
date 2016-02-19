from datetime import datetime, timedelta
import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import TimedPluginBase

HELP_TEXT = '''
A plugin to remind you of things.
Usage:
glados remind me in 8 minutes to check rosh
glados remind me at 7:00am to wake up
'''.strip()

REMIND_RE = re.compile(r'glados,? remind me ((?P<at_t>at '
                       r'(?P<hour>\d+):(?P<min>\d+)(?P<ampm>a|p)m)|'
                       r'(?P<in_t>in (?P<number>\d+) '
                       r'(?P<unit>minutes?|hours?|days?|weeks?))) '
                       r'(?P<what>.*)', re.I)


class RemindMe(TimedPluginBase):
    help_text = HELP_TEXT
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
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return REMIND_RE.match(msg['text'])

    def handle_message(self, msg):
        msg_match = REMIND_RE.match(msg['text'])

        event = Event(user=self.users[msg['user']],
                      channel=msg['channel'])

        now = datetime.now()
        if msg_match.group('in_t'):
            unit = msg_match.group('unit')
            if not unit.endswith('s'):
                unit = unit + 's'
            td_args = {
                unit: int(msg_match.group('number'))
            }
            time = datetime.now() + timedelta(**td_args)
        else:
            hour = int(msg_match.group('hour'))
            if msg_match.group('ampm') == 'p':
                hour += 12
            minute = int(msg_match.group('min'))
            time = now.replace(hour=hour, minute=minute)
            if time < now:
                time = time + timedelta(days=1)
        remind_what = msg_match.group('what')
        event.what = remind_what
        event.time = time
        self.db_session.add(event)
        self.db_session.commit()

        time_fmt = 'at {}'.format(time.strftime('%I:%M%P'))
        if time.date() != now.date():
            if time.date() - now.date() == timedelta(days=1):
                time_fmt = 'tomorrow {}'.format(time_fmt)
            elif time.date() - now.date() < timedelta(days=7):
                time_fmt = '{} {}'.format(time.strftime('%A'), time_fmt)
            else:
                time_fmt = '{} {}'.format(time.strftime('%b %d'), time_fmt)
        self.send('Okay, I\'ll remind you {} {}'.format(
            time_fmt, remind_what), msg['channel'])

    def run_timed_event(self):
        events = self.db_session.query(Event).all()
        now = datetime.now()
        for event in events:
            if event.time < now:
                self.send(
                    '@{}, you asked me to remind you {}'.format(event.user,
                                                                event.what),
                    event.channel)
                self.db_session.delete(event)
        self.db_session.commit()


class Event(Base):
    __tablename__ = 'event'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user = sqlalchemy.Column(sqlalchemy.String)
    channel = sqlalchemy.Column(sqlalchemy.String)
    what = sqlalchemy.Column(sqlalchemy.String)
    time = sqlalchemy.Column(sqlalchemy.DateTime)
