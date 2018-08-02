import unittest
from mock import patch
from watchmen.manhattan_hourly import main, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestManhattanHourlyWatchmen(unittest.TestCase):

    def setUp(self):
        self.example_empty_list = []
        self.example_failed_list = ['example_feed']
        self.example_exception_message = "Something went wrong"

    @patch('watchmen.manhattan_hourly.raise_alarm')
    @patch('watchmen.manhattan_hourly.Watchmen.process_hourly_feeds_metrics')
    @patch('watchmen.manhattan_hourly.Watchmen.get_dynamo_hourly_time_string')
    def test_main(self, mock_time_string, mock_process_feeds, mock_alarm):
        mock_process_feeds.return_value = self.example_empty_list, self.example_empty_list
        # Test when all feeds are up and running
        expected_result = SUCCESS_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when one of the feeds are down
        mock_process_feeds.return_value = self.example_failed_list, self.example_empty_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when one of the feeds submitted abnormal amounts of domains
        mock_process_feeds.return_value = self.example_empty_list, self.example_failed_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when both a feed is down and a feed submits abnormal amounts of domains
        mock_process_feeds.return_value = self.example_failed_list, self.example_failed_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when exception occurs is processing feeds
        mock_process_feeds.return_value = Exception(self.example_exception_message)
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
