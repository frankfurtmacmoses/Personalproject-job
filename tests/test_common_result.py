"""
test_common_result.py
"""
from mock import MagicMock, patch
import os
import unittest

from watchmen.common.result import Result
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)


class TestResult(unittest.TestCase):
    def setUp(self):
        """
        setup for test
        """
        self.test_path = os.path.dirname(os.path.realpath(__file__))
        self.test_data_path = os.path.join(self.test_path, 'data')
        self.test_json_name = 'test_result_to_dict.json'
        self.test_json_directory = os.path.join(self.test_data_path, self.test_json_name)
        self.expected_json = {
            "disable_notifier": False,
            "details": {
                "source": "Jupiter", "target": "Sockeye", "time": "2019-06-27T18"},
            "result_id": 9012018,
            "message": "Endpoint count is below minimum. "
                       "There is no need to check or something is wrong with endpoint file.",
            "source": "Jupiter",
            "state": "FAILURE",
            "subject": "Jupiter: Failure in checking endpoint",
            "target": "Sockeye",
            "time": "2019-06-27T18",
        }
        self.example_arg = {
            "disable_notifier": False,
            "details": {
                "source": "Jupiter", "target": "Sockeye", "time": "2019-06-27T18"},
            "result_id": 9012018,
            "message": "Endpoint count is below minimum. "
                       "There is no need to check or something is wrong with endpoint file.",
            "source": "Jupiter",
            "state": "FAILURE",
            "subject": "Jupiter: Failure in checking endpoint",
            "target": "Sockeye",
        }
        self.example_time_string = '2019-06-27T18'
        pass

    @patch('watchmen.common.result.datetime')
    def test_to_dict(self, mock_datetime):
        """
        test watchmen.common.result :: Result :: to_dict
        @return:
        """
        # Python built-in types are immutable, therefore datetime cannot be mocked
        mock_dt = MagicMock()
        mock_datetime.utcnow.return_value = mock_dt
        mock_dt.isoformat.return_value = self.example_time_string

        obj = Result(**self.example_arg)
        result = obj.to_dict()
        result["time"] = self.example_time_string
        self.assertDictEqual(result, self.expected_json)
        pass
