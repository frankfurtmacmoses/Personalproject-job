"""
watchmen/common/notifier.py

This interface uses the result object in order to send notifications.

@author: Jinchi Zhang
@email: jzhang@infoblox.com
@created: July 3, 2019
"""
from abc import ABCMeta, abstractmethod


class Notifier(metaclass=ABCMeta):
    """
    Notifier class sends notification.
    """

    def __init__(self):
        """
        Constructor of Notifier interface.
        """
        raise NotImplementedError

    @abstractmethod
    def notify(self, topic=str):
        """
        Each notifier must implement this method.
        Otherwise it will cause the following error: NotImplementedError

        @param topic: <str> the topic arn to be notified.
        """
        raise NotImplementedError
