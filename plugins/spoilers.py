import re

from bs4 import BeautifulSoup
import requests
import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import TimedPluginBase

HELP_TEXT = '''
A plugin to fetch spoilers.
You can optionally subscribe to be notified of new spoilers.
Usage:
glados subscribe
glados unsubscribe
'''.strip()
MTG_CHANNEL_NAME = 'magic'
ALL_CARDS_URL = 'http://mythicspoiler.com/newspoilers.html'
CARD_URL = 'http://mythicspoiler.com/{}/cards/{}.html'
CARD_URL_RE = re.compile(r'([a-z]+)/cards/([a-z]+)\.html')
SUBSCRIBE_RE = re.compile(r'glados (un)?subscribe', re.I)


def fetch_card_list():
    page = requests.get(ALL_CARDS_URL)
    if page.status_code != requests.codes.ok:
        return []

    def is_card(tag):
        if tag.name != 'a':
            return False
        if 'href' not in tag.attrs:
            return False
        return CARD_URL_RE.match(tag['href'])

    soup = BeautifulSoup(page.text, 'html.parser')
    card_links = soup.find_all(is_card)
    cards = []
    for card in card_links:
        match = CARD_URL_RE.match(card['href'])
        cards.append(CARD_URL.format(match.group(1), match.group(2)))
    return cards


def fetch_card_name(url):
    page = requests.get(url)
    if page.status_code != requests.codes.ok:
        return 'Name not available'
    soup = BeautifulSoup(page.text, 'html.parser')
    return soup.find('title').string.split('|')[0].strip()


class FetchSpoilers(TimedPluginBase):
    help_text = HELP_TEXT
    interval = '* * * * *'

    def __init__(self, *args, **kwargs):
        self.channels = {}
        self.magic_channel = None
        super().__init__(*args, **kwargs)

    def setup(self):
        for channel_id, channel_name in self.channels.items():
            if channel_name == MTG_CHANNEL_NAME:
                self.magic_channel = channel_id
                return

    def can_handle_message(self, msg):
        if msg['type'] != 'message':
            return False
        if 'message' in msg:
            return False
        return SUBSCRIBE_RE.match(msg['text'])

    def handle_message(self, msg):
        match = SUBSCRIBE_RE.match(msg['text'])
        user_name = self.users[msg['user']]
        if match.group(1) is None:  # subscribe
            existing = self.db_session.query(Subscription).filter_by(
                user=user_name
            ).first()
            if existing:
                self.send('You are already subscribed.',
                          '@{}'.format(user_name))
            else:
                new_sub = Subscription(user=user_name)
                self.db_session.add(new_sub)
                self.send('You have successfully been subscribed.',
                          '@{}'.format(user_name))
        else:
            existing = self.db_session.query(Subscription).filter_by(
                user=user_name
            ).first()
            if existing:
                self.db_session.delete(existing)
                self.send('You have successfully been unsubscribed.',
                          '@{}'.format(user_name))
            else:
                self.send('You are not subscribed.',
                          '@{}'.format(user_name))

        self.db_session.commit()

    def run_timed_event(self):
        all_cards = fetch_card_list()
        new_cards = []
        for card_url in all_cards:
            existing = self.db_session.query(Card).filter_by(
                url=card_url
            ).first()
            if not existing:
                card_name = fetch_card_name(card_url)
                new_card = Card(
                    name=card_name,
                    url=card_url,
                    image_url=card_url.replace('.html', '.jpg')
                )
                self.db_session.add(new_card)
                new_cards.append(new_card)
        if not new_cards:
            return
        subscriptions = self.db_session.query(Subscription).all()
        for sub in subscriptions:
            message = None
            if len(new_cards) == 1:
                message = 'New spoiler: {}'.format(new_cards[0].name)
            else:
                card_list = ''.join(
                    ['\n- {}'.format(card.name) for card in new_cards]
                )
                message = 'New spoilers: {}'.format(card_list)
            self.send(message, '@{}'.format(sub.user))
        for card in new_cards:
            attachment = {
                'fallback': card.name,
                'title': card.name,
                'title_link': card.url,
                'image_url': card.image_url,
            }
            self.send('', self.magic_channel, [attachment])
        self.db_session.commit()


class Card(Base):
    __tablename__ = 'card'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    url = sqlalchemy.Column(sqlalchemy.String)
    image_url = sqlalchemy.Column(sqlalchemy.String)


class Subscription(Base):
    __tablename__ = 'spoilersubscription'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    user = sqlalchemy.Column(sqlalchemy.String)
