import unittest
from mock import patch, MagicMock
from moto import mock_s3
from watchmen.utils.universal_watchman import Watchmen
from botocore.exceptions import ClientError


class TestUniversalWatchman(unittest.TestCase):

    def setUp(self):
        self.example_bucket = "example_bucket"
        self.example_path = "some/path/here"
        self.example_content_length_zero = {'ContentLength': 0}
        self.example_content_length = {'ContentLength': 200}
        self.example_file = "{Number: 5}"
        self.watcher = Watchmen()

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
        returned_result = self.watcher.validate_file_on_s3(self.example_bucket, self.example_path)
        self.assertEqual(expected_result, returned_result)
        # Test when file is size of zero
        s3_object.get = MagicMock(return_value=self.example_content_length_zero)
        expected_result = False
        returned_result = self.watcher.validate_file_on_s3(self.example_bucket, self.example_path)
        self.assertEqual(expected_result, returned_result)
        # Test when file is non-zero size
        s3_object.get = MagicMock(return_value=self.example_content_length)
        expected_result = True
        returned_result = self.watcher.validate_file_on_s3(self.example_bucket, self.example_path)
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
        returned_result = self.watcher.get_file_contents_s3(self.example_bucket, self.example_path)
        self.assertEqual(expected_result, returned_result)
