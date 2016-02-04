import re

import sqlalchemy

from plugin_base import DeclarativeBase as Base
from plugin_base import GladosPluginBase

HELP_TEXT = '''
Group plugin. Allows you to notify groups of users.
Commands:
glados create group NAME
glados delete group NAME
glados add USER|me to group NAME
glados remove USER|me from group NAME
glados help groups
glados list groups (pm)
glados show group NAME (pm)
Notify groups with @NAME in a message.
'''.strip()

create_re = re.compile(r'glados(?:,)? create group (\w+)', re.I)
delete_re = re.compile(r'glados(?:,)? delete group (\w+)', re.I)
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

    def create_or_get_user(self, userid):
        existing = self.db_session.query(GroupUser).filter_by(
            user_id=userid
        ).first()
        if existing:
            return existing
        user = GroupUser(user_id=userid, name=self.users[userid])
        self.db_session.add(user)
        self.db_session.commit()
        return user

    def get_id_for_user(self, name):
        for user_id, username in self.users.items():
            if username == name:
                return user_id
        return None

    def create_group(self, groupname, user, channel):
        existing = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if existing:
            self.send(
                'Failure: cannot create @{}. '
                'Group already exists.'.format(groupname),
                channel
            )
            return
        owner = self.create_or_get_user(user)
        new_group = Group(name=groupname, owner=owner, users=[owner])
        self.db_session.add(new_group)
        self.db_session.commit()
        self.send('Success: group @{} created.'.format(groupname), channel)

    def delete_group(self, groupname, user, channel):
        group = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if not group:
            self.send(
                'Failure: cannot delete @{}. '
                'Group does not exist.'.format(groupname),
                channel
            )
            return
        user = self.create_or_get_user(user)
        if user != group.owner:
            self.send(
                'Failure: cannot delete @{}. '
                'Only the group owner can delete the group.'.format(groupname),
                channel
            )
            return
        self.db_session.delete(group)
        self.db_session.commit()
        self.send('Success: group @{} deleted.'.format(groupname), channel)

    def add_to_group(self, name, groupname, user, channel):
        group = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if not group:
            self.send(
                'Failure: cannot add user to @{}. '
                'Group does not exist.'.format(groupname),
                channel
            )
            return
        if name == 'me':
            user_id = user
        else:
            user_id = self.get_id_for_user(name)
            if user_id is None:
                self.send(
                    'Failure: cannot add user to @{}. '
                    'User does not exist.'.format(groupname),
                    channel
                )
                return
        user = self.create_or_get_user(user_id)
        name = user.name
        if user in group.users:
            self.send(
                'Failure: cannot add user to @{}. '
                'User is already in group.'.format(groupname),
                channel
            )
            return
        group.users.append(user)
        self.db_session.commit()
        self.send('Success: {} added to @{}.'.format(name, groupname), channel)

    def remove_from_group(self, name, groupname, user, channel):
        group = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if not group:
            self.send(
                'Failure: cannot remove user from @{}. '
                'Group does not exist.'.format(groupname),
                channel
            )
            return
        if name == 'me':
            user_id = user
        else:
            user_id = self.get_id_for_user(name)
            if user_id is None:
                self.send(
                    'Failure: cannot remove user from @{}. '
                    'User does not exist.'.format(groupname),
                    channel
                )
                return
        if name != 'me' and user != group.owner.user_id:
            self.send(
                'Failure: cannot remove user from @{}. '
                'Only that user and the owner can do that.'.format(groupname),
                channel
            )
            return

        user = self.create_or_get_user(user_id)
        name = user.name
        if user == group.owner:
            self.send(
                'Failure: cannot remove user from @{}. '
                'User is owner of group.'.format(groupname),
                channel
            )
            return

        if user not in group.users:
            self.send(
                'Failure: cannot remove user from @{}. '
                'User is not in group.'.format(groupname),
                channel
            )
            return
        group.users.remove(user)
        self.db_session.commit()
        self.send(
            'Success: {} removed from @{}.'.format(name, groupname),
            channel
        )

    def help_groups(self, user, channel):
        self.send(HELP_TEXT, channel)

    def list_groups(self, user, channel):
        groups = self.db_session.query(Group).all()
        group_list = ', '.join(_.name for _ in groups)
        self.send(
            'Groups: {}'.format(group_list),
            '@{}'.format(self.users[user])
        )

    def group_info(self, groupname, user, channel):
        group = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if not group:
            self.send(
                'Failure: cannot show info for @{}. '
                'Group does not exist.'.format(groupname),
                channel
            )
            return
        member_list = ', '.join(_.name for _ in group.users)
        self.send(
            'Group @{}: owner {}. Members: {}'.format(
                groupname,
                group.owner.name,
                member_list
            ),
            '@{}'.format(self.users[user])
        )

    def notify_group(self, groupname, user, channel):
        group = self.db_session.query(Group).filter_by(
            name=groupname
        ).first()
        if not group:
            return
        for group_user in group.users:
            self.send(
                'User @{} has notified group @{} in channel #{}'.format(
                    self.users[user],
                    groupname,
                    self.channels[channel]
                ),
                '@{}'.format(group_user.name)
            )

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
                handler(
                    *match.groups(),
                    user=msg['user'],
                    channel=msg['channel']
                )
                return


group_user_association = sqlalchemy.Table(
    'g_gu_assoc',
    Base.metadata,
    sqlalchemy.Column('group_id', sqlalchemy.ForeignKey('group.id')),
    sqlalchemy.Column('user_id', sqlalchemy.ForeignKey('groupuser.id'))
)


class Group(Base):
    __tablename__ = 'group'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String, unique=True)
    owner = sqlalchemy.orm.relationship('GroupUser', back_populates='owned')
    onwer_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('groupuser.id')
    )

    users = sqlalchemy.orm.relationship(
        'GroupUser',
        secondary=group_user_association
    )


class GroupUser(Base):
    __tablename__ = 'groupuser'
    __table_args__ = {'sqlite_autoincrement': True}
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    user_id = sqlalchemy.Column(sqlalchemy.String, unique=True)
    owned = sqlalchemy.orm.relationship('Group', back_populates='owner')
