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
        self.static_time = datetime(year=2018, month=12, day=18)
        self.result_time = '2018-12-18'
        self.result_args = {
            "details": "ERROR: 2018/12/gt_mpdns_20181217.zip could not be found in "
                       "cyber-intel/hancock/georgia_tech/! Please check S3 and Georgia "
                       "Tech logs!",
            "disable_notifier": False,
            "dt_created": self.static_time,
            "dt_updated": self.static_time,
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": None,
            "source": "Spectre",
            "state": "FAILURE",
            "subject": "Spectre Georgia Tech data monitor detected a failure!",
            "success": False,
            "target": "Georgia Tech S3",
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
        test2["dt_created"] = test2["dt_updated"] = self.static_time

        tests = [{
            "args": test1
        }, {
            "args": test2
        }]
        for idx, test in enumerate(tests):
            args = test['args']
            result_obj = Result(**args)
            expected = copy.deepcopy(self.result_args)
            dt_created = args.get('dt_created')
            expected['dt_created'] = self.result_time if dt_created is None else dt_created.isoformat()
            dt_updated = args.get('dt_updated')
            expected['dt_updated'] = self.result_time if dt_updated is None else dt_updated.isoformat()
            LOGGER.info('Test %02d: %s', idx, args)
            result = result_obj.to_dict()
            self.assertDictEqual(result, expected)
        pass
