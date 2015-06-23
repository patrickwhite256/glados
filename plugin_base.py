from sqlalchemy.ext.declarative import declarative_base

DeclarativeBase = declarative_base()


class GladosPluginBase(object):
    consumes_message = False  # set true if the event should not continue propogating

    def __init__(self, db_session, send_fn):
        self.send = send_fn
        self.db_session = db_session

    def setup(self):
        """
            Perform any necessary setup before this plugin runs
        """
        pass

    def teardown(self):
        """
            Perform any necessary teardown before this plugin exits
            The DB session will be committed, so you don't have to worry about that.
        """
        pass

    def can_handle_message(self, msg):
        """
            Return something that evaluates to true if this plugin should handle this message.
        """
        return False

    def handle_message(self, msg):
        """
            Handle the message
        """
        pass
