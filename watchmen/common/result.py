"""
# common/result.py

# author: jzhang@infoblox.com
# 2019-6-27
"""
from datetime import datetime

from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

DEFAULT_DISABLE_NOTIFIER = False
DEFAULT_DETAILS = {}
DEFAULT_RESULT_ID = 0
DEFAULT_MESSAGE = 'DEFAULT MESSAGE'
DEFAULT_SOURCE = 'DEFAULT_SOURCE'
DEFAULT_STATE = "DEFAULT_STATE"
DEFAULT_SUBJECT = 'DEFAULT SUBJECT'
DEFAULT_TARGET = 'DEFAULT TARGET'


class Result:
    """
    Result is a database class containing result properties
    """

    def __init__(self,
                 disable_notifier=DEFAULT_DISABLE_NOTIFIER,
                 details=DEFAULT_DETAILS,
                 result_id=DEFAULT_RESULT_ID,
                 message=DEFAULT_MESSAGE,
                 source=DEFAULT_SOURCE,
                 state=DEFAULT_STATE,
                 subject=DEFAULT_SUBJECT,
                 target=DEFAULT_TARGET,
                 time=datetime.utcnow()):
        """
        Constructor of class Result
        @param disable_notifier: whether the notifier should be disabled, boolean
        @param details: details for short notifications, dict
        @param result_id: id of the result, int
        @param message: message for long notification, str
        @param source: source of information, meanly the name of watchmen, str
        @param state: state of the target, str
        @param subject: subject to be sent for long notification, str
        @param target: name of the target being monitored, str
        @param time: time when generated, datetime
        """
        self.disable_notifier = disable_notifier
        self.details = details
        self.result_id = result_id
        self.message = message
        self.source = source
        self.state = state
        self.subject = subject
        self.target = target
        self.time = time
        LOGGER.info('A result has been generated, '
                    '\nresult id: {}, '
                    '\nsource name: {}'
                    '\ntime: {}'.format(self.result_id, self.source, self.time))
        pass

    def to_dict(self):
        """
        output the result properties to a json file
        @return: whether the whole process succeeded, boolean
        """
        dict_data = {
            "disable_notifier": self.disable_notifier,
            "details": self.details,
            "result_id": self.result_id,
            "message": self.message,
            "source": self.source,
            "state": self.state,
            "subject": self.subject,
            "target": self.target,
            "time": self.time.isoformat(),
        }
        return dict_data
        pass
