from sqlalchemy.ext.declarative import declarative_base

DeclarativeBase = declarative_base()


class GladosPluginBase(object):
    consumes_message = False  # set true if the event should not continue propogating

    def __init__(self, db_session, send_fn, **kwargs):
        self.send = send_fn
        self.db_session = db_session
        for attr_name, attr in kwargs.items():
            setattr(self, attr_name, attr)

    def setup(self):
        '''
            Perform any necessary setup before this plugin runs
        '''
        pass

    def teardown(self):
        '''
            Perform any necessary teardown before this plugin exits
            The DB session will be committed, so you don't have to worry about that.
        '''
        pass

    def can_handle_message(self, msg):
        '''
            Return something that evaluates to true if this plugin should handle this message.
        '''
        raise NotImplementedError

    def handle_message(self, msg):
        '''
            Handle the message
        '''
        raise NotImplementedError

    @property
    def help_text(self):
        '''
            Return text giving help about this plugin.
            Will be accessed by 'glados help PLUGIN' (lower cased)
            The 'plugin_name' property will be used.
            Otherwise, the plugin class name will be used.
            Subclasses MUST implement this.
        '''
        raise NotImplementedError('You must implement a help function')

    @property
    def plugin_name(self):
        '''
            Return a friendly name of this plugin.
        '''
        return self.__class__.__name__
