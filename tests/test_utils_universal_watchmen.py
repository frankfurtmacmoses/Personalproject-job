import unittest
import pytz
from datetime import datetime
from mock import patch, MagicMock
from moto import mock_s3, mock_dynamodb
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

    @patch('watchmen.utils.universal_watchmen.Watchmen.get_feed_metrics')
    def test_process_feed_metrics(self, mock_get_feed_metrics):
        # Test when metric is within range
        mock_get_feed_metrics.return_value = self.example_get_metric_return
        expected_result = [], []
        returned_result = self.watcher.process_hourly_feeds_metrics(
            self.example_feeds_to_check, self.example_table_name
        )
        self.assertEqual(expected_result, returned_result)
        # Test when metric is out of range (too high)
        mock_get_feed_metrics.return_value = self.example_get_metric_return_high
        expected_result = [], ['test_feed']
        returned_result = self.watcher.process_hourly_feeds_metrics(
            self.example_feeds_to_check, self.example_table_name
        )
        self.assertEqual(expected_result, returned_result)
        # Test when metric is out of range (too low)
        mock_get_feed_metrics.return_value = self.example_get_metric_return_low
        expected_result = [], ['test_feed']
        returned_result = self.watcher.process_hourly_feeds_metrics(
            self.example_feeds_to_check, self.example_table_name
        )
        self.assertEqual(expected_result, returned_result)
        # Test when metric is None
        mock_get_feed_metrics.return_value = None
        expected_result = ['test_feed'], []
        returned_result = self.watcher.process_hourly_feeds_metrics(
            self.example_feeds_to_check, self.example_table_name
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

    @patch('watchmen.utils.universal_watchmen.datetime')
    def test_get_dynamo_hourly_time_string(self, mock_datetime):
        mock_datetime.now.return_value = self.example_now
        # Test for a time string for dynamo db setup one hour ago
        expected_result = self.example_time_string
        returned_result = self.watcher.get_dynamo_hourly_time_string()
        self.assertEqual(expected_result, returned_result)
