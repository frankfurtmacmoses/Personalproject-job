import unittest
from watchmen.process.moloch import main, check_for_existing_files, SUCCESS_MESSAGE, \
                            FAILURE_DOMAIN, FAILURE_BOTH, FAILURE_HOSTNAME
from mock import patch
from moto import mock_s3
import datetime
import pytz


class TestMoloch(unittest.TestCase):

    def setUp(self):
        self.year = 2017
        self.month = 5
        self.day = 24
        self.hour = 8
        self.minute = 0
        self.example_now = datetime.datetime(
            year=self.year, month=self.month, day=self.day,
            hour=self.hour, minute=self.minute, tzinfo=pytz.utc)
        self.example_file_path = 'somepath/to/a/file'
        self.example_exception_msg = "Something went wrong :("
        self.example_event = {}
        self.example_context = {}

    @mock_s3
    @patch('watchmen.process.moloch.Watchmen.validate_file_on_s3')
    def test_check_for_existing_files(self, mock_watcher):
        mock_watcher.return_value = False
        # Test when no file found on S3
        expected_result = False
        returned_result = check_for_existing_files(self.example_file_path, self.example_now)
        self.assertEqual(expected_result, returned_result)
        # Test when the file exists and works
        mock_watcher.return_value = True
        expected_result = True
        returned_result = check_for_existing_files(self.example_file_path, self.example_now)
        self.assertEqual(expected_result, returned_result)
        # Test first 3 missing files, but finally one is found
        mock_watcher.side_effect = [False, False, False, True]
        expected_result = True
        returned_result = check_for_existing_files(self.example_file_path, self.example_now)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.moloch.raise_alarm')
    @patch('watchmen.process.moloch.check_for_existing_files')
    def test_main(self, mock_check, mock_alarm):
        # Test when both feeds are up
        mock_check.side_effect = [True, True]
        expected_result = SUCCESS_MESSAGE
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        # Test when both feeds are down
        mock_check.side_effect = [False, False]
        expected_result = FAILURE_BOTH
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        # Test when domain feed is down
        mock_check.side_effect = [False, True]
        expected_result = FAILURE_DOMAIN
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        # Test when hostname feed is down
        mock_check.side_effect = [True, False]
        expected_result = FAILURE_HOSTNAME
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        # Test when exception is thrown
        mock_check.side_effect = Exception(self.example_exception_msg)
        expected_result = FAILURE_BOTH
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
