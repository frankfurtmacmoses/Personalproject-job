import unittest
from mock import patch

from watchmen.common.sum_result import SummarizedResult
from watchmen.process.generic_watchmen import NOT_IMPLEMENTED_MESSAGE, RESULTS_TYPE_ERROR
from watchmen.process.generic_watchmen import Watchmen


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
        self.assertEqual(str(error.exception), NOT_IMPLEMENTED_MESSAGE)

    @patch('watchmen.process.generic_watchmen.raise_alarm')
    def test_notify(self, mock_alarm):
        tests = [
            {
                "success": True,
                "expected": self.example_message_body
            },
            {
                "success": False,
                "expected": self.example_subject_message
            },
            {
                "success": False,
                "expected": self.example_subject_message,
                "pager": self.example_pager_topic
            },
            {
                "success": False,
                "expected": self.example_subject_message,
                "pager": self.example_pager_topic,
                "pager_message": "test"
            }
        ]

        for test in tests:
            expected = test.get('expected')
            result = SummarizedResult(
                success=test.get('success'), message=self.example_message_body, subject=self.example_subject_message)
            if test.get('pager_message'):
                result.result.update({"pager_message": test.get("pager_message")})
            returned = self.example_watchmen.notify(
                res_dict=result, sns_topic=self.example_topic, pager_topic=test.get('pager'))
            self.assertEqual(expected, returned)

    @patch('watchmen.process.generic_watchmen.raise_alarm')
    def test_notify_failures(self, mock_alarm):
        non_dict_tests = [4, 4.5, "cake", 'x', False, [1, 2], {"This": "is  dict"}, None]

        # Ensure the all types besides a dict will fail
        for test in non_dict_tests:
            with self.assertRaises(TypeError) as error:
                self.example_watchmen.notify(test, self.example_topic)
            self.assertEqual(str(error.exception), RESULTS_TYPE_ERROR)
