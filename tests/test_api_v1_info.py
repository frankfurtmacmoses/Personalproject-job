"""
# test_api_v1_info
"""
import os
import logging
import unittest

from mock import patch
from watchmen.api.v1.info import get_api_doc
from watchmen.api.v1.info import get_info


class ApiInfoTester(unittest.TestCase):
    """
    ApiInfoTester includes all unit tests for watchmen.api.v1.info module
    """

    @classmethod
    def teardown_class(cls):
        logging.shutdown()

    def setUp(self):
        """setup for test"""
        test_path = os.path.dirname(os.path.realpath(__file__))
        proj_path = os.path.dirname(test_path)
        self.spec_path = os.path.join(
            proj_path, 'watchmen', 'apidoc', 'v1')
        pass

    def tearDown(self):
        """tearing down at the end of the test"""
        pass

    @patch('watchmen.api.v1.info.flask')
    def test_get_api_doc(self, mock_flask):
        """
        test watchmen.api.v1.info.get_api_doc
        """
        get_api_doc()
        mock_flask.send_from_directory.assert_called_with(
            self.spec_path, 'swagger.yaml',
            as_attachment=True,
            attachment_filename='swagger-watchmen.yaml',
            mimetype='application/octet-stream'
        )
        pass

    @patch('watchmen.api.v1.info.flask')
    def test_get_info(self, mock_flask):
        """
        test watchmen.api.v1.info.get_info
        """
        result = get_info()
        self.assertEqual(result.get('name'), 'Watchmen Project')
