"""
test_common_result.py
"""
from datetime import datetime
from mock import patch, MagicMock
import unittest

from watchmen.common.result import Result
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class TestResult(unittest.TestCase):
    def setUp(self):
        """
        setup for test
        """
        self.static_time = datetime(year=2019, month=5, day=29)
        self.result_time = '2019-09-23'
        self.result_args = {
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
        pass

    @patch('watchmen.common.result.datetime')
    def test_to_dict(self, mock_datetime):
        """
        test watchmen.common.result :: Result :: to_dict
        @return:
        """
        mock_dt = MagicMock()
        mock_dt.isoformat.return_value = self.result_time
        mock_datetime.utcnow.return_value = mock_dt

        import copy
        test1 = copy.deepcopy(self.result_args)
        test2 = copy.deepcopy(self.result_args)
        test2['observed_time'] = self.static_time

        tests = [{
            "args": test1
        }, {
            "args": test2
        }]
        for idx, test in enumerate(tests):
            args = test['args']
            resultObj = Result(**args)
            expected = copy.deepcopy(self.result_args)
            dt = args.get('observed_time')
            expected['observed_time'] = self.result_time if dt is None else dt.isoformat()
            LOGGER.info('Test %02d: %s', idx, args)
            result = resultObj.to_dict()
            self.assertDictEqual(result, expected)
        pass
