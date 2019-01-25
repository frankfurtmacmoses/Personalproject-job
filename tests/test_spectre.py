import unittest
from watchmen.spectre import main, get_s3_filename
from datetime import datetime

import pytz
from mock import patch
from moto import mock_s3

from watchmen.spectre import SUCCESS_MESSAGE


class TestSpectre(unittest.TestCase):

    def setUp(self):
        self.example_yesterday = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_filename = "2018/12/gt_mpdns_20181217.zip"

    @patch('watchmen.spectre.datetime')
    def test_get_s3_filename(self, mock_datetime):
        mock_datetime.now.return_value = self.example_yesterday
        expected_result = self.example_filename
        returned_result = get_s3_filename()
        self.assertEqual(expected_result, returned_result)

    @mock_s3
    @patch('watchmen.spectre.raise_alarm')
    @patch('watchmen.spectre.Watchmen.validate_file_on_s3')
    @patch('watchmen.spectre.get_s3_filename')
    @patch('watchmen.spectre.Watchmen')
    def test_main(self,mock_watchman, mock_filename, mock_validate, mock_alarm):
        mock_filename.return_value = self.example_filename
        # File exists
        mock_validate.return_value = True
        expected_result = '{} {}'.format(SUCCESS_MESSAGE, self.example_filename)
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)




