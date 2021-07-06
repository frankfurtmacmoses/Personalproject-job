"""
test watchmen.common.storage_service.py
"""
from mock import patch
import unittest

from watchmen.common.storage_service import StorageService


class TestStorageService(unittest.TestCase):

    def setUp(self):
        """
        setup for test
        """
        self.test_results = [{
            "target": "Threatwave"
        }, {
            "target": "Psl"
        }, {
            "target": "Cyber-Intel Endpoints"
        }]
        self.path = "WatchmenResults/year=2021/month=06/day=16"
        self.bucket = "cyber-intel-test"

    def test__init__(self):
        """
        test watchmen.common.storage_service :: StorageService :: __init__
        """
        pass

    @patch('watchmen.common.storage_service.StorageService._save_to_s3')
    def test_save_results(self, mock_save):
        """
           test watchmen.common.storage_service :: StorageService :: save_results
           """
        storage_service_obj = StorageService()
        storage_service_obj._save_to_s3(self.bucket)
        mock_save.assert_called()

        # When bucket name is empty
        storage_service_obj._save_to_s3()
        mock_save.assert_called()

    @patch('watchmen.utils.s3')
    def test_save_to_s3(self, mock_s3):
        """
        test watchmen.common.storage_service :: StorageService :: _save_to_s3
        """
        class TestResult:
            def __init__(self, val):
                self.target = val['target']

        results = [TestResult(result) for result in self.test_results]
        storage_service_obj = StorageService()
        mock_s3.create_key(results, self.path, bucket=self.bucket)
        storage_service_obj._save_to_s3(results, bucket=self.bucket)
        mock_s3.create_key.assert_called_with(results, self.path, bucket=self.bucket)

        # test exception
        storage_service_obj = StorageService()
        returned = storage_service_obj._save_to_s3(None, None)
        expected = None
        self.assertEqual(expected, returned)
