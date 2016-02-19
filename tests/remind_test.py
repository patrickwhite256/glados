# pylint: disable=redefined-outer-name
from unittest.mock import Mock

import pytest
import sqlalchemy

from plugins import remind
from plugin_base import DeclarativeBase as Base


def format_message(message, user_id='PATRICK', channel_id='CHANNEL'):
    return {
        'type': 'message',
        'text': message,
        'user': user_id,
        'channel': channel_id
    }


@pytest.fixture(scope='module')
def plugin():
    # use in-memory
    engine = sqlalchemy.create_engine('sqlite://')
    Base.metadata.create_all(engine)
    session_cls = sqlalchemy.orm.sessionmaker(engine)
    session = session_cls()
    send_fn = Mock()
    # user id => user name
    users = {
        'PATRICK': 'patrick',
    }
    channels = {
        'CHANNEL': 'general'
    }
    return remind.RemindMe(
        session,
        send_fn,
        users=users,
        channels=channels
    )

TEST_PHRASES_GOOD = [
    'glados, remind me in 10 minutes to do something',
    'GLaDOS remind me in 10 hours to wake up',
    'GLaDOS, remind me at 5:30am to kill the rooster',
    'glados remind me at 12:30pm to buy another rooster'
]


def test_can_handle_messages(plugin):
    for message in TEST_PHRASES_GOOD:
        assert plugin.can_handle_message(format_message(message))


# TODO: use freezegun and actually test this
