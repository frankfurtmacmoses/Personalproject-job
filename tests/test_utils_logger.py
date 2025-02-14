"""
# test_utils_logger

@author: Jason Zhu
@email: jason_zhuyx@hotmail.com

"""
import logging
import unittest

from watchmen.utils.logger_formatter import factory
from watchmen.utils.logger import get_logger
from watchmen.utils.logger import print_info
from watchmen.utils.logger import raise_ni

LOGGER = get_logger(__name__)


class LoggerTests(unittest.TestCase):
    """
    LoggerTests includes all unit tests for watchmen.urils.logger module
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

    def test_formatter_factory(self):
        """
        test watchmen.utils.logger_formatter.factory
        """
        err_logger = logging.getLogger(__name__)
        err_logger.addHandler(logging.StreamHandler())
        err_handler = err_logger.handlers[0]
        err_handler.setFormatter(fmt=factory(use_color=False))
        err_logger.info('Logging information (no color) ...')
        err_handler.setFormatter(fmt=factory())
        err_logger.info('Logging information ...')
        err_logger.fatal('Logging fail ...')
        err_logger.error('Logging error ...')
        err_logger.warning('Logging warning ...')
        err_logger.debug('Logging debug ...')

    def test_get_logger(self):
        """
        test watchmen.utils.logger.get_logger
        """
        print_info()
        # removing prefix for `python -m unitest`
        logger_name = '.'.join(LOGGER.name.split('.')[-2:])
        self.assertEqual(logger_name, __name__)
        LOGGER.debug('LOGGER name: %s', LOGGER.name)
        LOGGER.warning('LOGGER warning ...')

    def test_raise_ni(self):
        """
        test watchmen.utils.logger.raise_ni
        """
        method_name = 'some_method_name'
        msg = 'must implement {} in derived class'.format(method_name)
        with self.assertRaises(NotImplementedError) as context:
            result = raise_ni(method_name)
            self.assertIsNone(result)
        self.assertEqual(msg, str(context.exception))
