import unittest
import datetime
import pytz
from mock import patch
from moto import mock_s3

from watchmen.process.moloch import FAILURE_DOMAIN, FAILURE_BOTH, FAILURE_HOSTNAME, EXCEPTION_SUBJECT, SUCCESS_MESSAGE
from watchmen.process.moloch import main, check_for_existing_files, get_check_results, notify


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
        self.example_results = False, True
        self.example_status = "The feeds were checked"

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
    def test_get_check_results(self, mock_check, mock_alarm):
        test_results = [
            {"domain": True, "hostname": True},
            {"domain": False, "hostname": True},
            {"domain": True, "hostname": False},
            {"domain": False, "hostname": False}
        ]

        for results in test_results:
            domain = results.get("domain")
            hostname = results.get("hostname")
            mock_check.side_effect = [domain, hostname]
            expected = domain, hostname
            returned = get_check_results()
            self.assertEqual(expected, returned)

        mock_check.side_effect = Exception(self.example_exception_msg)
        expected = None, None
        returned = get_check_results()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.moloch.notify')
    @patch('watchmen.process.moloch.get_check_results')
    def test_main(self, mock_check, mock_notify):
        mock_check.return_value = self.example_results
        mock_notify.return_value = self.example_status
        # Get the results from checking the feeds
        results = mock_check()
        self.assertIsNotNone(results)
        mock_check.assert_called_with()
        # Send them through notify
        status = mock_notify()
        self.assertIsNotNone(status)
        mock_notify.assert_called_with()

        # If nothing caused an exception
        expected = self.example_status
        returned = main(None, None)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.moloch.raise_alarm')
    def test_notify(self, mock_alarm):
        test_results = [
            {"domain": True, "hostname": True, "expected": SUCCESS_MESSAGE},
            {"domain": False, "hostname": True, "expected": FAILURE_DOMAIN},
            {"domain": True, "hostname": False, "expected": FAILURE_HOSTNAME},
            {"domain": False, "hostname": False, "expected": FAILURE_BOTH},
            {"domain": None, "hostname": False, "expected": EXCEPTION_SUBJECT},
            {"domain": False, "hostname": None, "expected": EXCEPTION_SUBJECT},
            {"domain": None, "hostname": None, "expected": EXCEPTION_SUBJECT}
        ]

        for results in test_results:
            domain = results.get("domain")
            hostname = results.get("hostname")
            expected = results.get("expected")
            returned = notify(domain, hostname)
            self.assertEqual(expected, returned)
