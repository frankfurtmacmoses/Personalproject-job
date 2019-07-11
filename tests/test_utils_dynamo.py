import unittest
import pytz
from datetime import datetime
from mock import patch
from watchmen.utils.dynamo import select_dynamo_time_string, get_dynamo_daily_time_string, \
    get_dynamo_hourly_time_string, get_dynamo_weekly_time_string


class TestDynamo(unittest.TestCase):

    def setUp(self):
        self.example_feed_name = 'test_feed'
        self.example_feeds_to_check = {'test_feed': {
            'metric_name': 'success',
            'min': 4,
            'max': 50,
            'hour_submitted': '10',
            'days_to_subtract': 4,
        }}
        self.example_now = datetime(
            year=2018, month=5, day=24,
            hour=5, minute=5, tzinfo=pytz.utc
        )
        self.example_one_day_ago_time_string = "2018-05-23T10"
        self.example_time_string = "2018-05-24T04"
        self.example_weekly_time_string = "2018-05-20T10"

    @patch('watchmen.utils.dynamo.get_dynamo_hourly_time_string')
    @patch('watchmen.utils.dynamo.get_dynamo_daily_time_string')
    @patch('watchmen.utils.dynamo.get_dynamo_weekly_time_string')
    def test_select_time_string(self, mock_weekly, mock_daily, mock_hourly):
        mock_hourly.return_value = self.example_time_string
        # Test when it's hourly feed
        expected_result = self.example_time_string
        returned_result = select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 0
        )
        self.assertEqual(expected_result, returned_result)
        # Test when it's daily feed
        mock_daily.return_value = self.example_time_string
        expected_result = self.example_time_string
        returned_result = select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 1
        )
        self.assertEqual(expected_result, returned_result)
        # Test when it's weekly feed
        mock_weekly.return_value = self.example_time_string
        expected_result = self.example_time_string
        returned_result = select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 2
        )
        self.assertEqual(expected_result, returned_result)
        # Test when user doesn't pick correct feed
        expected_result = None
        returned_result = select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, None
        )
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.dynamo.datetime')
    def test_get_dynamo_daily_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup one day ago
        expected_result = self.example_one_day_ago_time_string
        returned_result = get_dynamo_daily_time_string(self.example_feeds_to_check.get(self.example_feed_name))
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.dynamo.datetime')
    def test_get_dynamo_hourly_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup one hour ago
        expected_result = self.example_time_string
        returned_result = get_dynamo_hourly_time_string(self.example_feeds_to_check.get(self.example_feed_name))
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.dynamo.datetime')
    def test_get_dynamo_weekly_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup on a particular day of the week
        expected_result = self.example_weekly_time_string
        returned_result = get_dynamo_weekly_time_string(self.example_feeds_to_check.get(self.example_feed_name))
        self.assertEqual(expected_result, returned_result)
