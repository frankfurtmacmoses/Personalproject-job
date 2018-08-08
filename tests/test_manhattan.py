from mock import patch
from moto import mock_sns
import unittest

from watchmen.manhattan import main, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'type': 'Daily'}
        self.example_event_hourly = {'type': 'Hourly'}
        self.example_event_weekly = {'type': 'Weekly'}
        self.example_feed_name = "example_feed"
        self.example_exception_msg = "Thingy stopped working"

    @mock_sns
    @patch('watchmen.manhattan.raise_alarm')
    @patch('watchmen.manhattan.Watchmen.process_feeds_metrics')
    def test_main(self, mock_process_feed, mock_alarm):
        # Test when hourly succeeds with no issues
        mock_process_feed.return_value = [], []
        expected_result = SUCCESS_MESSAGE
        returned_result = main(self.example_event_hourly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when hourly has downed feeds
        mock_process_feed.return_value = [self.example_feed_name], []
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_hourly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when hourly has abnormal submission rate from feeds
        mock_process_feed.return_value = [], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_hourly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when hourly has both abnormal and downed feeds
        mock_process_feed.return_value = [self.example_feed_name], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_hourly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when hourly has an exception thrown
        mock_process_feed.side_effect = Exception(self.example_exception_msg)
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_hourly, None)
        self.assertEqual(expected_result, returned_result)

        # Test when daily succeeds with no issues
        mock_process_feed.side_effect = None
        mock_process_feed.return_value = [], []
        expected_result = SUCCESS_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)
        # Test when daily has downed feeds
        mock_process_feed.return_value = [self.example_feed_name], []
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)
        # Test when daily has abnormal submission rate from feeds
        mock_process_feed.return_value = [], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)
        # Test when daily has both abnormal and downed feeds
        mock_process_feed.return_value = [self.example_feed_name], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)
        # Test when daily has an exception thrown
        mock_process_feed.side_effect = Exception(self.example_exception_msg)
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)

        # Test when weekly succeeds with no issues
        mock_process_feed.side_effect = None
        mock_process_feed.return_value = [], []
        expected_result = SUCCESS_MESSAGE
        returned_result = main(self.example_event_weekly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when weekly has downed feeds
        mock_process_feed.return_value = [self.example_feed_name], []
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_weekly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when weekly has abnormal submission rate from feeds
        mock_process_feed.return_value = [], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_weekly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when weekly has both abnormal and downed feeds
        mock_process_feed.return_value = [self.example_feed_name], [self.example_feed_name]
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_weekly, None)
        self.assertEqual(expected_result, returned_result)
        # Test when weekly has an exception thrown
        mock_process_feed.side_effect = Exception(self.example_exception_msg)
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event_daily, None)
        self.assertEqual(expected_result, returned_result)
