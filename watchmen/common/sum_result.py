"""
watchmen/common/sum_result.py

@author: Kayla Ramos
@email: kramos@infoblox.com
@date: 2019-10-06
"""
from watchmen.utils.logger import get_logger


MESSAGE_TYPE_ERROR_MESSAGE = "Message MUST be a string message!"
SUBJECT_TYPE_ERROR_MESSAGE = "Subject MUST be a string message!"
SUCCESS_TYPE_ERROR_MESSAGE = "Success MUST be a bool!"
MESSAGE_VALUE_ERROR_MESSAGE = "Message CANNOT be empty!"
SUBJECT_VALUE_ERROR_MESSAGE = "Subject CANNOT be empty!"

LOGGER = get_logger('watchmen.' + __name__)


class SummarizedResult(object):
    """
    SummarizedResult is dictionary that contains information about any check and
    stores the information in an organized manner. This dictionary is used primarily for notifications
    with AWS SNS and for keeping track of information that the creator deems valuable.
    """

    def __init__(self, success, message, subject):
        """
        Constructor for watchmen.common.SummarizedResult
        """
        if not isinstance(success, bool):
            raise TypeError(SUCCESS_TYPE_ERROR_MESSAGE)
        if not isinstance(message, str):
            raise TypeError(MESSAGE_TYPE_ERROR_MESSAGE)
        if not isinstance(subject, str):
            raise TypeError(SUBJECT_TYPE_ERROR_MESSAGE)

        if not message:
            raise ValueError(MESSAGE_VALUE_ERROR_MESSAGE)
        if not subject:
            raise ValueError(SUBJECT_VALUE_ERROR_MESSAGE)

        self.result = {
            "success": success,
            "message": message,
            "subject": subject
        }

    def add_kv(self, key, value):
        """
        Add a new key-value pair to the results. The key-value pairs are for extra information
        that is helpful for clarifying the state of the check. They usually aid in the notification process.

        Example added key-value pairs:
        pager_message: 'Please check the Watchmen'
        last_failed: True
        skip_on_success: True

        @param key: to be added
        @param value: to be added
        """
        self.result.update({key: value})

    def log_result(self):
        """
        Log the result dictionary on a line by line basis so reading the content is easy.
        @return:
        """
        for key, value in iter(self.result.items()):
            LOGGER.info("{}: {}".format(key, value))
