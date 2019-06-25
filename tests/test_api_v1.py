"""
# test_api_v1
"""
import logging
import unittest
import mock

from watchmen.api_v1 import getInfo
from watchmen.api_v1 import getApiDoc


class ApiRouteTester(unittest.TestCase):
    """
    ApiRouteTester includes all unit tests for watchmen.api_v1 module
    """

    @classmethod
    def teardown_class(cls):
        logging.shutdown()

    def setUp(self):
        """setup for test"""
        pass

    def tearDown(self):
        """tearing down at the end of the test"""
        pass

    @mock.patch('watchmen.api_v1.info')
    def test_info_functions(self, mock_info):
        getInfo()
        mock_info.get_info.assert_called()
        getApiDoc()
        mock_info.get_api_doc.assert_called()
        pass
