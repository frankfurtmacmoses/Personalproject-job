import unittest
from mock import patch

from watchmen.common.sum_result import SummarizedResult
from watchmen.utils.universal_watchmen import NOT_IMPLEMENTED_MESSAGE, RESULTS_TYPE_ERROR
from watchmen.utils.universal_watchmen import Watchmen


class TestUniversalWatchman(unittest.TestCase):

    def setUp(self):
        self.example_topic = "1234FakeTopic"
        self.example_pager_topic = "5678ExtraFake"
        self.example_watchmen = Watchmen()
        self.example_message_body = "Important information"
        self.example_subject_message = "Snazzy subject"

    def test_monitor(self):
        with self.assertRaises(NotImplementedError) as error:
            self.example_watchmen.monitor()
        self.assertEqual(error.exception.message, NOT_IMPLEMENTED_MESSAGE)

    @patch('watchmen.utils.universal_watchmen.raise_alarm')
    def test_notify(self, mock_alarm):
        non_dict_tests = [4, 4.5, "cake", 'x', False, [1, 2], {"This": "is  dict"}, None]

        success_true_test = SummarizedResult(
            success=True, message=self.example_message_body, subject=self.example_subject_message)

        success_false_test = SummarizedResult(
            success=False, message=self.example_message_body, subject=self.example_subject_message)

        # Test Success True
        expected = self.example_message_body
        returned = self.example_watchmen.notify(res_dict=success_true_test, sns_topic=self.example_topic)
        self.assertEqual(expected, returned)

        # Test Success False
        expected = self.example_subject_message
        returned = self.example_watchmen.notify(res_dict=success_false_test, sns_topic=self.example_topic)
        self.assertEqual(expected, returned)

        # Test Success False with Pager topic
        expected = self.example_subject_message
        returned = self.example_watchmen.notify(
            res_dict=success_false_test, sns_topic=self.example_topic, pager_topic=self.example_pager_topic)
        self.assertEqual(expected, returned)

        # Ensure the all types besides a dict will fail
        for test in non_dict_tests:
            with self.assertRaises(TypeError) as error:
                self.example_watchmen.notify(test, self.example_topic)
            self.assertEqual(error.exception.message, RESULTS_TYPE_ERROR)
