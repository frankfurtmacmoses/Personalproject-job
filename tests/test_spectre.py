import unittest
from datetime import datetime
import pytz

from mock import patch
from moto import mock_s3
from watchmen.process.spectre import SUCCESS_MESSAGE, FAILURE_MESSAGE, EXCEPTION_MESSAGE
from watchmen.process.spectre import main, get_s3_filename, check_if_found_file, notify


class TestSpectre(unittest.TestCase):

    def setUp(self):
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_filename = "2018/12/gt_mpdns_20181217.zip"
        self.example_exception_message = "Something is not working"
        self.example_status = "The file was checked"

    @patch('watchmen.process.spectre.raise_alarm')
    @patch('watchmen.process.spectre.Watchmen.validate_file_on_s3')
    def test_check_if_found_file(self, mock_validate, mock_alarm):
        # File exists
        mock_validate.return_value = True
        expected = True
        returned = check_if_found_file(self.example_filename)
        self.assertEqual(expected, returned)

        # File does not exist
        mock_validate.return_value = False
        expected = False
        returned = check_if_found_file(self.example_filename)
        self.assertEqual(expected, returned)

        # Exception occurred
        mock_validate.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = check_if_found_file(self.example_filename)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.spectre.datetime')
    def test_get_s3_filename(self, mock_datetime):
        mock_datetime.now.return_value = self.example_today
        expected_result = self.example_filename
        returned_result = get_s3_filename()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.spectre.notify')
    @patch('watchmen.process.spectre.check_if_found_file')
    def test_main(self, mock_check, mock_notify):
        mock_check.return_value = False
        mock_notify.return_value = self.example_status

        # Get the result from checking the file
        result = mock_check()
        self.assertIsNotNone(result)
        mock_check.assert_called_with()
        # Send them through notify
        status = mock_notify()
        self.assertIsNotNone(status)
        mock_notify.assert_called_with()

        # Return check status
        expected = self.example_status
        returned = main(None, None)
        self.assertEqual(expected, returned)

    @mock_s3
    @patch('watchmen.process.spectre.raise_alarm')
    def test_notify(self, mock_alarm):
        test_results = [
            {"found": True, "expected": SUCCESS_MESSAGE},
            {"found": False, "expected": 'ERROR: {}{}'.format(self.example_filename, FAILURE_MESSAGE)},
            {"found": None, "expected": 'ERROR: {}-{}'.format(EXCEPTION_MESSAGE, self.example_filename)}
        ]

        for result in test_results:
            found = result.get("found")
            expected = result.get("expected")
            returned = notify(found, self.example_filename)
            self.assertEqual(expected, returned)
