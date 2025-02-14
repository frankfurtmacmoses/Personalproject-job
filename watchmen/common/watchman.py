"""
common/watchman.py

This is an interface that all watchmen must utilize

@author: Jinchi Zhang
@email: jzhang@infoblox.com
@created: July 1, 2019
"""
from abc import ABCMeta, abstractmethod

from watchmen.common.result_svc import Result
from watchmen.utils.logger import get_logger
from watchmen.config import settings


class Watchman(metaclass=ABCMeta):
    """
    Watchman interface
    """

    # State Strings
    STATE = {
        "success": "SUCCESS",
        "exception": "EXCEPTION",
        "failure": "FAILURE",
        "recovered": "RECOVERED",
    }

    def __init__(self):
        """
        Constructor of Watchman class
        """
        self.watchman_name = self.__class__.__name__
        self.logger = get_logger(self.watchman_name, settings('logging.level', 'INFO'))
        pass

    @abstractmethod
    def monitor(self) -> [Result]:
        """
        Each watchman must implement this method.
        Otherwise it will cause the following error: NotImplementedError

        This method contains the monitoring process unique to each watchman.

        @return: <Result> result
        """
        raise NotImplementedError
