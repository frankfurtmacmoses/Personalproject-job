"""
common/result_svc.py
"""
from watchmen.common.result import Result
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class ResultSvc:
    """
    The ResultSvc class is the service to process result generated from checker eg. store them to data base
    """

    def __init__(self, result: Result):
        """
        Constructor of ResultSvc class
        """
        self.result = result
