"""
# test_main
"""
from watchmen.process.configs.endpoints import DATA
import logging
import unittest


class EndpointsTester(unittest.TestCase):
    """
    Endpoints.py tester that makes sure all local paths have "path" as a variable.
    """

    @classmethod
    def teardown_class(cls):
        logging.shutdown()

    """
    Test endpoints.py to make sure all endpoints have a path variable.
    """
    def test_local_endpoints(self):
        bad_endpoint_found = False

        for endpoint in DATA:
            if not endpoint.get('path'):
                bad_endpoint_found = True

        self.assertEqual(False, bad_endpoint_found)
