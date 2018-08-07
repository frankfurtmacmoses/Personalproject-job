import unittest
from mock import patch
from watchmen.manhattan_daily import main, SUCCESS_MESSAGE, FAILURE_MESSAGE, Watchmen
from moto import mock_sns


class TestManhattanHourlyWatchmen(unittest.TestCase):

    def setUp(self):
        self.example_empty_list = []
        self.example_bucket = "example_bucket"
        self.example_failed_list = ['example_feed']
        self.example_exception_message = "Something went wrong"
        self.example_feeds_to_check = {'test_feed': {'metric_name': 'success', 'min': 4, 'max': 50}}
        self.example_table_name = 'table'
        self.watcher = Watchmen(self.example_bucket)
        self.example_get_metric_return = {'success': 40}
        self.example_get_metric_return_low = {'success': 3}
        self.example_get_metric_return_high = {'success': 500}

    @mock_sns
    @patch('watchmen.manhattan_daily.raise_alarm')
    @patch('watchmen.manhattan_daily.Watchmen.process_feeds_metrics')
    @patch('watchmen.manhattan_daily.Watchmen.get_dynamo_daily_time_string')
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
