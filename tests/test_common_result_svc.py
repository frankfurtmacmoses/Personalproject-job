"""
test_common_result_svc.py
"""
from datetime import datetime
import unittest

from watchmen.common.result import Result
from watchmen.common.result_svc import ResultSvc
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class TestResultSvc(unittest.TestCase):
    def setUp(self):
        """
        setup for test
        """
        self.example_time = datetime(year=2019, month=9, day=29)
        self.test_result_arg = {
            "details": {
                "source": "Jupiter", "target": "Sockeye", "time": "2019-06-27T18"},
            "disable_notifier": False,
            "message": "Endpoint count is below minimum. "
                       "There is no need to check or something is wrong with endpoint file.",
            "result_id": 9012018,
            "success": False,
            "source": "Jupiter",
            "state": "FAILURE",
            "subject": "Jupiter: Failure in checking endpoint",
            "target": "Sockeye",
        }
        self.test_result = Result(**self.test_result_arg)
        pass

    def test__init__(self):
        """
        test watchmen.common.result_svc.__init__
        @return:
        """
        result_svc_obj = ResultSvc(self.test_result)
        self.assertIsNotNone(result_svc_obj.result)
        self.assertEqual(result_svc_obj.result.result_id, 9012018)
        pass
