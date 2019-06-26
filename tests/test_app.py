"""
# test_app
"""
import logging
import unittest

from mock import patch
from watchmen.app import application


class AppTester(unittest.TestCase):
    """
    AppTester includes all unit tests for watchmen.app module
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

    def test_app(self):
        self.assertIsNotNone(application)
        pass

    @patch('watchmen.app_connexion.app_main')
    def test_main(self, mock_app_main):
        import runpy
        result = runpy.run_module('watchmen.app', run_name='__main__')
        self.assertEqual(result['__name__'], '__main__')
        # print('main result:', result)
        mock_app_main.assert_called()
        pass
