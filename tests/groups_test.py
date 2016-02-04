from unittest.mock import Mock

import pytest
import sqlalchemy

from plugins import groups
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
    Session = sqlalchemy.orm.sessionmaker(engine)
    session = Session()
    send_fn = Mock()
    # user id => user name
    users = {
        'PATRICK': 'patrick',
        'ALICIA': 'alicia',
        'SOREY': 'sorey',
        'ROSE': 'rose',
        'MIKLEO': 'mikleo',
        'LAILAH': 'lailah',
        'DEZEL': 'dezel',
        'EDNA': 'edna'
    }
    channels = {
        'LADYLAKE': 'ladylake',
        'CHANNEL': 'general'
    }
    return groups.Groups(
        session,
        send_fn,
        users=users,
        channels=channels
    )


def test_can_handle_messages(plugin):
    messages = [
        'glados, create group people',
        'glados add me to group hello123',
        'Glados, remove person1337 from group lulz',
        'GLaDOS help groups',
        'glados list groups',
        'glados show group devs',
        '@bloops: hello',
        'do the @bloops want to talk'
    ]

    for message in messages:
        assert plugin.can_handle_message(format_message(message))


def test_can_create_group(plugin):
    plugin.handle_message(format_message(
        'glados create group testers'
    ))
    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'created' in plugin.send.call_args[0][0].lower()


def test_cannot_create_existing_group(plugin):
    plugin.handle_message(format_message(
        'glados create group badz'
    ))
    plugin.handle_message(format_message(
        'glados create group badz'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'already' in plugin.send.call_args[0][0].lower()


def test_add_me_to_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_add',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add me to group test_add',
        user_id='LAILAH'
    ))

    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'added' in plugin.send.call_args[0][0].lower()


def test_add_other_to_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_add',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add sorey to group test_add',
        user_id='ALICIA'
    ))
    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'added' in plugin.send.call_args[0][0].lower()


def test_cannot_add_already_in_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_add_fail',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add me to group test_add_fail',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'already' in plugin.send.call_args[0][0].lower()


def test_cannot_add_does_not_exist(plugin):
    plugin.handle_message(format_message(
        'glados add me to group test_add_not_exist',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


def test_cannot_add_user_does_not_exist(plugin):
    plugin.handle_message(format_message(
        'glados create group test_add_user_not_exist',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados add zaveid to group test_add_user_not_exist',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


# TODO, maybe: username removed themself from this group.


def test_can_remove_user_from_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add mikleo to group test_remove',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados remove mikleo from group test_remove',
        user_id='ALICIA'
    ))
    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'removed' in plugin.send.call_args[0][0].lower()


def test_can_remove_self_from_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove_self',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add mikleo to group test_remove_self',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados remove me from group test_remove_self',
        user_id='MIKLEO'
    ))
    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'removed' in plugin.send.call_args[0][0].lower()


def test_cannot_remove_other_user_from_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove_other',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados add mikleo to group test_remove_other',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados remove mikleo from group test_remove_other',
        user_id='EDNA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'owner' in plugin.send.call_args[0][0].lower()


def test_owner_cannot_remove_self_from_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove_owner',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados remove me from group test_remove_owner',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'owner' in plugin.send.call_args[0][0].lower()

    plugin.handle_message(format_message(
        'glados remove alicia from group test_remove_owner',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'owner' in plugin.send.call_args[0][0].lower()


def test_cannot_remove_person_not_in_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove_not_in',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados remove dezel from group test_remove_not_in',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'not in' in plugin.send.call_args[0][0].lower()

    plugin.handle_message(format_message(
        'glados remove me from group test_remove_not_in',
        user_id='DEZEL'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'not in' in plugin.send.call_args[0][0].lower()


def test_cannot_remove_from_nonexistent_group(plugin):
    plugin.handle_message(format_message(
        'glados remove me from group test_remove_not_exist',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


def test_cannot_remove_user_does_not_exist(plugin):
    plugin.handle_message(format_message(
        'glados create group test_remove_user_not_exist',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados remove zaveid from group test_add_user_not_exist',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


def test_can_delete_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_delete',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados delete group test_delete',
        user_id='ALICIA'
    ))
    assert 'success' in plugin.send.call_args[0][0].lower()
    assert 'deleted' in plugin.send.call_args[0][0].lower()

# TODO: add "are you sure" prompt


def test_cannot_delete_nonexistent_group(plugin):
    plugin.handle_message(format_message(
        'glados delete group test_not_exist',
        user_id='ALICIA'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


def test_cannot_delete_not_owner(plugin):
    plugin.handle_message(format_message(
        'glados delete group test_not_owner',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados delete group test_not_owner',
        user_id='ROSE'
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'owner' in plugin.send.call_args[0][0].lower()


def test_list_groups(plugin):
    plugin.handle_message(format_message(
        'glados create group test_list_one',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados create group test_list_two',
        user_id='ALICIA'
    ))

    plugin.handle_message(format_message(
        'glados list groups',
        user_id='ALICIA'
    ))
    assert 'test_list_one' in plugin.send.call_args[0][0].lower()
    assert 'test_list_two' in plugin.send.call_args[0][0].lower()
    assert plugin.send.call_args[0][1] != 'CHANNEL'


def test_list_my_groups(plugin):
    plugin.handle_message(format_message(
        'glados create group test_my_list_one',
        user_id='DEZEL'
    ))
    plugin.handle_message(format_message(
        'glados create group test_my_list_two',
        user_id='DEZEL'
    ))
    plugin.handle_message(format_message(
        'glados create group test_my_list_three',
        user_id='EDNA'
    ))
    plugin.handle_message(format_message(
        'glados list my groups',
        user_id='DEZEL'
    ))
    assert 'test_my_list_one' in plugin.send.call_args[0][0].lower()
    assert 'test_my_list_two' in plugin.send.call_args[0][0].lower()
    assert not 'test_my_list_three' in plugin.send.call_args[0][0].lower()
    assert plugin.send.call_args[0][1] != 'CHANNEL'


def test_show_group(plugin):
    plugin.handle_message(format_message(
        'glados create group test_show',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados add rose to group test_show',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados add mikleo to group test_show',
        user_id='ALICIA'
    ))
    plugin.handle_message(format_message(
        'glados show group test_show'
    ))
    assert 'test_show' in plugin.send.call_args[0][0].lower()
    assert 'owner' in plugin.send.call_args[0][0].lower()
    assert 'alicia' in plugin.send.call_args[0][0].lower()
    assert 'rose' in plugin.send.call_args[0][0].lower()
    assert 'mikleo' in plugin.send.call_args[0][0].lower()
    assert plugin.send.call_args[0][1] != 'CHANNEL'


def test_show_nonexistant_group(plugin):
    plugin.handle_message(format_message(
        'glados show group test_show_dne',
    ))
    assert 'failure' in plugin.send.call_args[0][0].lower()
    assert 'exist' in plugin.send.call_args[0][0].lower()


def test_help_groups(plugin):
    plugin.handle_message(format_message(
        'glados help groups',
        user_id='ALICIA'
    ))

    assert 'create' in plugin.send.call_args[0][0].lower()
    assert 'delete' in plugin.send.call_args[0][0].lower()
    assert 'remove' in plugin.send.call_args[0][0].lower()
    assert 'add' in plugin.send.call_args[0][0].lower()
    assert 'help' in plugin.send.call_args[0][0].lower()
    assert 'list' in plugin.send.call_args[0][0].lower()
    assert 'show' in plugin.send.call_args[0][0].lower()


def test_notifies_group_members(plugin):
    plugin.handle_message(format_message(
        'glados create group seraphim',
        user_id='EDNA'
    ))
    plugin.handle_message(format_message(
        'glados add mikleo to group seraphim',
        user_id='EDNA'
    ))
    plugin.handle_message(format_message(
        'glados add me to group seraphim',
        user_id='DEZEL'
    ))
    plugin.handle_message(format_message(
        'glados add me to group seraphim',
        user_id='LAILAH'
    ))

    plugin.send.reset_mock()

    plugin.handle_message(format_message(
        'man @seraphim kinda suck',
        user_id='SOREY',
        channel_id='LADYLAKE'
    ))
    assert len(plugin.send.call_args_list) == 4
    for args in plugin.send.call_args_list:
        assert 'notif' in args[0][0]
        assert '@seraphim' in args[0][0]
        assert 'sorey' in args[0][0]
        assert '#ladylake' in args[0][0]
        assert args[0][1] != 'LADYLAKE'
