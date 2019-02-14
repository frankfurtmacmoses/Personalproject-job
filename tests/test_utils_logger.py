"""
# test_utils_logger

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com

"""
import unittest

from watchmen.utils.logger import get_logger
from watchmen.utils.logger import raise_ni


class LoggerTests(unittest.TestCase):
    """
    LoggerTests includes all unit tests for logger module
    """
    def setUp(self):
        return

    def tearDown(self):
        return

    def test_get_logger(self):
        """
        test_get_logger tests logger.get_logger() function
        """
        logger = get_logger(__name__)
        self.assertEqual(logger.propagate, True)
        self.assertEqual(logger.name, __name__)

    def test_raise_ni(self):
        """
        test_raise_ni tests logger.raise_ni() function
        """
        msg = 'must implement whatever_name in derived class'
        with self.assertRaises(NotImplementedError) as context:
            raise_ni("whatever_name")
        self.assertEqual(msg, context.exception.message)
