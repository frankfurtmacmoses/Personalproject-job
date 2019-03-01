import unittest
import pytz
from datetime import datetime
from mock import patch, MagicMock
from moto import mock_s3, mock_dynamodb, mock_cloudwatch
from watchmen.utils.universal_watchmen import Watchmen
from botocore.exceptions import ClientError


class TestUniversalWatchman(unittest.TestCase):

    def setUp(self):
        self.example_bucket = "example_bucket"
        self.example_path = "some/path/here"
        self.example_content_length_zero = {'ContentLength': 0}
        self.example_content_length = {'ContentLength': 200}
        self.example_file = "{Number: 5}"
        self.example_now = datetime(
            year=2018, month=5, day=24,
            hour=5, minute=5, tzinfo=pytz.utc
        )
        self.example_time_string = "2018-05-24T04"
        self.example_one_day_ago_time_string = "2018-05-23T09"
        self.example_weekly_time_string = "2018-05-20T10"
        self.watcher = Watchmen(self.example_bucket)
        self.example_feed_name = 'test_feed'
        self.example_table_name = 'table'
        self.example_empty_metric = {}
        self.example_failed_metric = {'Items': [{'source': 'No feed', 'metric': {'who': 2}}]}
        self.example_metric = {'Items': [{'source': self.example_feed_name, 'metric': {'IPV4': 1}}]}
        self.example_returned_metric = {'IPV4': 1}
        self.example_feeds_to_check = {'test_feed': {'metric_name': 'success', 'min': 4, 'max': 50}}
        self.example_get_metric_return = {'success': 40}
        self.example_get_metric_return_low = {'success': 3}
        self.example_get_metric_return_high = {'success': 500}
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

    @mock_s3
    def test_validate_file_on_s3(self):
        mock_get = MagicMock(side_effect=ClientError({}, {}))
        s3_object = MagicMock()
        s3_object.get = mock_get
        client = MagicMock()
        client.Object = MagicMock(return_value=s3_object)
        self.watcher.s3_client = client
        # Test when file is not found
        expected_result = False
        returned_result = self.watcher.validate_file_on_s3(self.example_path)
        self.assertEqual(expected_result, returned_result)
        # Test when file is size of zero
        s3_object.get = MagicMock(return_value=self.example_content_length_zero)
        expected_result = False
        returned_result = self.watcher.validate_file_on_s3(self.example_path)
        self.assertEqual(expected_result, returned_result)
        # Test when file is non-zero size
        s3_object.get = MagicMock(return_value=self.example_content_length)
        expected_result = True
        returned_result = self.watcher.validate_file_on_s3(self.example_path)
        self.assertEqual(expected_result, returned_result)

    @mock_s3
    @patch('boto3.resource')
    def test_get_file_contents_s3(self, mock_boto3):
        s3_object = MagicMock(side_effect=ClientError({}, {}))
        client = MagicMock()
        client.Object = MagicMock(return_value=s3_object)
        mock_boto3.return_value = client
        # Test when file contents could not be retrieved
        expected_result = None
        returned_result = self.watcher.get_file_contents_s3(self.example_path)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.universal_watchmen.Watchmen.get_dynamo_hourly_time_string')
    @patch('watchmen.utils.universal_watchmen.Watchmen.get_dynamo_daily_time_string')
    @patch('watchmen.utils.universal_watchmen.Watchmen.get_dynamo_weekly_time_string')
    def test_get_time_string(self, mock_weekly, mock_daily, mock_hourly):
        mock_hourly.return_value = self.example_time_string
        # Test when it's hourly feed
        expected_result = self.example_time_string
        returned_result = self.watcher.select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 0
        )
        self.assertEqual(expected_result, returned_result)
        # Test when it's daily feed
        mock_daily.return_value = self.example_time_string
        expected_result = self.example_time_string
        returned_result = self.watcher.select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 1
        )
        self.assertEqual(expected_result, returned_result)
        # Test when it's weekly feed
        mock_weekly.return_value = self.example_time_string
        expected_result = self.example_time_string
        returned_result = self.watcher.select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, 2
        )
        self.assertEqual(expected_result, returned_result)
        # Test when user doesn't pick correct feed
        expected_result = None
        returned_result = self.watcher.select_dynamo_time_string(
            self.example_feeds_to_check, self.example_feed_name, None
        )
        self.assertEqual(expected_result, returned_result)

    @mock_dynamodb
    def test_get_feed_metrics(self):
        table_object = MagicMock()
        table_object.query.return_value = self.example_metric
        self.watcher.dynamo_client.Table = MagicMock(return_value=table_object)
        # Test for feed with a valid metric
        expected_result = self.example_returned_metric
        returned_result = self.watcher.get_feed_metrics(
            self.example_table_name, self.example_feed_name, self.example_now
        )
        self.assertEqual(expected_result, returned_result)
        # Test for feed without a metric
        table_object.query.return_value = self.example_failed_metric
        expected_result = self.example_empty_metric
        returned_result = self.watcher.get_feed_metrics(
            self.example_table_name, self.example_feed_name, self.example_now
        )
        self.assertEqual(expected_result, returned_result)

    @mock_cloudwatch
    @patch('watchmen.utils.universal_watchmen.Watchmen')
    def test_process_feed_logs(self, mock_watchmen):
        self.watcher.log_client = MagicMock()
        tests = [
            {
                'start':  datetime(
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
            self.watcher.log_client.describe_log_streams.return_value = test.get('log_response')
            result = self.watcher.process_feeds_logs(test.get('feeds'), test.get('start'), test.get('end'))
            self.assertEqual(test.get('expected'), result)

    @patch('watchmen.utils.universal_watchmen.Watchmen.get_feed_metrics')
    @patch('watchmen.utils.universal_watchmen.Watchmen.select_dynamo_time_string')
    def test_process_feeds_metrics(self, mock_time_string, mock_get_feed_metrics):
        mock_get_feed_metrics.return_value = self.example_get_metric_return
        expected_result = []
        returned_result = self.watcher.process_feeds_metrics(self.example_feeds_to_check, self.example_table_name, 0)
        self.assertEqual(expected_result, returned_result)
        mock_get_feed_metrics.return_value = self.example_get_metric_return_low
        expected_result = ['test_feed, Amount Submitted: 3, Min Submission Amount 4, Max Submission Amount : 50']
        returned_result = self.watcher.process_feeds_metrics(self.example_feeds_to_check, self.example_table_name, 0)
        self.assertEqual(expected_result, returned_result)
        mock_get_feed_metrics.return_value = self.example_get_metric_return_high
        expected_result = ['test_feed, Amount Submitted: 500, Min Submission Amount 4, Max Submission Amount : 50']
        returned_result = self.watcher.process_feeds_metrics(self.example_feeds_to_check, self.example_table_name, 0)
        self.assertEqual(expected_result, returned_result)
        mock_get_feed_metrics.return_value = None
        expected_result = []
        returned_result = self.watcher.process_feeds_metrics(self.example_feeds_to_check, self.example_table_name, 0)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.universal_watchmen.datetime')
    def test_get_dynamo_daily_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup one day ago
        expected_result = self.example_one_day_ago_time_string
        returned_result = self.watcher.get_dynamo_daily_time_string('09')
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.universal_watchmen.datetime')
    def test_get_dynamo_hourly_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup one hour ago
        expected_result = self.example_time_string
        returned_result = self.watcher.get_dynamo_hourly_time_string()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.utils.universal_watchmen.datetime')
    def test_get_dynamo_weekly_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup on a particular day of the week
        expected_result = self.example_weekly_time_string
        returned_result = self.watcher.get_dynamo_weekly_time_string('10', 4)
        self.assertEqual(expected_result, returned_result)
