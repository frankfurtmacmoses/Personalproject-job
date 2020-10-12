import unittest
from watchmen.common.notifiers_prod import SNS


class TestNotifiersTest(unittest.TestCase):

    def test_SNS(self):
        self.assertTrue(SNS, True)
