import unittest
import pytz
from datetime import datetime
from mock import patch
from moto import mock_dynamodb, mock_cloudwatch
from watchmen.utils.feeds import VALUE_ERROR_MESSAGE
from watchmen.utils.feeds import \
    get_feed_metrics, \
    process_feeds_logs, \
    process_feeds_metrics


class TestFeeds(unittest.TestCase):
    def setUp(self):
        self.example_empty_metric = {}
        self.example_failed_metric = {'Items': [{'source': 'No feed', 'metric': {'who': 2}}]}
        self.example_feed_name = 'test_feed'
        self.example_feeds_to_check = \
            [{
                "name": "test_feed",
                "source_name": "test_feed_source",
                "metric_name": "metric_name",
                "min": 4,
                "max": 50,
                "hour_submitted": "11",
                "needs_metric": True
            }]
        self.example_get_metric_return = {'metric_name': 40}
        self.example_get_metric_return_low = {'metric_name': 3}
        self.example_get_metric_return_high = {'metric_name': 500}
        # The first lastEventTimestamp set exactly between 4-5 and the second at 3:30 which succeeds.
        self.example_log_response = {
            'logStreams': [
                {
                    'logStreamName': 'test-feed/test-feed-prod/abc', 'lastEventTimestamp': 1546317000000
                },
                {
                    'logStreamName': 'garbage/noway', 'lastEventTimestamp': 1546313400000
                },
            ]
        }
        # The first lastEventTimestamp set exactly at 3:30 and will cause failure checking between 4-5.
        self.example_log_response_fail = {
            'logStreams': [
                {
                    'logStreamName': 'test-feed/test-feed-prod/abc', 'lastEventTimestamp': 1546313400000
                }
            ]
        }
        self.example_metric = {'Items': [{'source': self.example_feed_name, 'metric': {'IPV4': 1}}]}
        self.example_now = datetime(
            year=2018, month=5, day=24,
            hour=5, minute=5, tzinfo=pytz.utc
        )
        self.example_returned_metric = {'IPV4': 1}
        self.example_table_name = 'table'

    @mock_dynamodb
    @patch('watchmen.utils.feeds.boto3.resource')
    def test_get_feed_metrics(self, mock_resource):
        mock_resource.return_value.Table.return_value.query.return_value = self.example_metric
        # Test for feed with a valid metric
        expected_result = self.example_returned_metric
        returned_result = get_feed_metrics(
            self.example_table_name, self.example_feed_name, self.example_now
        )
        self.assertEqual(expected_result, returned_result)

        # Test for feed without a metric
        mock_resource.return_value.Table.return_value.query.return_value = self.example_failed_metric
        expected_result = self.example_empty_metric
        returned_result = get_feed_metrics(
            self.example_table_name, self.example_feed_name, self.example_now
        )
        self.assertEqual(expected_result, returned_result)

    @mock_cloudwatch
    @patch('watchmen.utils.feeds.boto3.client')
    def test_process_feed_logs(self, mock_client):
        tests = [
            {
                'start': datetime(
                    year=2019, month=1, day=1, hour=4, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
                ),
                'end': datetime(
                    year=2019, month=1, day=1, hour=5, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
                ),
                'expected': [],
                'log_response': self.example_log_response,
                'feeds': ['test-feed'],
            },
            {
                'start': datetime(
                    year=2019, month=1, day=1, hour=4, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
                ),
                'end': datetime(
                    year=2019, month=1, day=1, hour=5, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
                ),
                'expected': ['test-feed'],
                'log_response': self.example_log_response_fail,
                'feeds': ['test-feed'],
            }
         ]
        for test in tests:
            mock_client.return_value.describe_log_streams.return_value = test.get('log_response')
            result = process_feeds_logs(test.get('feeds'), test.get('start'), test.get('end'))
            self.assertEqual(test.get('expected'), result)

    @mock_cloudwatch
    @patch('watchmen.utils.feeds.boto3.client')
    def test_process_feed_logs_failure(self, mock_client):
        start_greater_than_end = {
            'start': datetime(
                year=2019, month=1, day=2, hour=4, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
            ),
            'end': datetime(
                year=2019, month=1, day=1, hour=5, minute=0, second=0, microsecond=0, tzinfo=pytz.utc
            ),
            'expected': ['test-feed'],
            'log_response': self.example_log_response_fail,
            'feeds': ['test-feed'],
        }

        with self.assertRaises(ValueError) as error:
            mock_client.return_value.describe_log_streams.return_value = start_greater_than_end.get('log_response')
            process_feeds_logs(start_greater_than_end.get('feeds'),
                               start_greater_than_end.get('start'),
                               start_greater_than_end.get('end'))
        self.assertEqual(VALUE_ERROR_MESSAGE, str(error.exception))

    @patch('watchmen.utils.feeds.datetime')
    @patch('watchmen.utils.feeds.get_feed_metrics')
    @patch('watchmen.utils.dynamo.select_dynamo_time_string')
    def test_process_feeds_metrics(self, mock_time_string, mock_get_feed_metrics, mock_datetime):
        mock_datetime.utcnow.return_value = self.example_now

        tests = [{
            "get_met": self.example_get_metric_return,
            "expected": ([], [])
        }, {
            "get_met": self.example_get_metric_return_low,
            "expected":
                (['test_feed_source:\n  Amount Submitted: 3, Min Submission Amount: 4, Max Submission Amount: 50'], [])
        }, {
            "get_met": self.example_get_metric_return_high,
            "expected":
                (['test_feed_source:\n  Amount Submitted: 500, Min Submission Amount: 4, Max Submission Amount: 50'],
                 [])
        }, {
            "get_met": None,
            "expected": ([], ["{}: {}".format(self.example_feed_name, self.example_now)])
        }]

        for test in tests:
            mock_get_feed_metrics.return_value = test.get("get_met")
            expected_result = test.get("expected")
            returned_result = process_feeds_metrics(self.example_feeds_to_check, self.example_table_name, 0)
            self.assertEqual(expected_result, returned_result)
