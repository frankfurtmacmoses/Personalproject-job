"""
tests/test_common_sns_notifier.py

@author: Jinchi Zhang
@email: jzhang@infoblox.com
@created: July 3, 2019
"""
import unittest
from mock import MagicMock, patch

from watchmen.common.sns_notifier import SnsNotifier


class TestSnsNotifier(unittest.TestCase):

    def setUp(self):
        pass

    @patch('watchmen.common.sns_notifier.raise_alarm')
    def test_notify(self, mock_raise):
        """
        test watchmen.common.sns_notifier :: Notifier :: notify
        @return:
        """
        tests = [{
            "subject": "subject string",
            "details": "details string",
            "arn": "arn0",
            "called_with": {
                "topic_arn": "arn0",
                "msg": "details string",
                "subject": "subject string",
            },
        }, {
            "subject": 3,
            "details": 7,
            "arn": "arn1",
            "called_with": {
                "topic_arn": "arn1",
                "msg": "7",
                "subject": "3",
            },
        }, {
            "subject": int,
            "details": int,
            "arn": "arn2",
            "called_with": {
                "topic_arn": "arn2",
                "msg": "<class 'int'>",
                "subject": "<class 'int'>",
            },
        }, {
            "subject": [1, 2, 3],
            "details": [4, 5, 6],
            "arn": "arn3",
            "called_with": {
                "topic_arn": "arn3",
                "msg": "[4, 5, 6]",
                "subject": "[1, 2, 3]",
            },
        }, {
            "subject": {"1": 1},
            "details": {"2": 2},
            "arn": "arn4",
            "called_with": {
                "topic_arn": "arn4",
                "msg": "{'2': 2}",
                "subject": "{'1': 1}",
            },
        }, {
            "subject": (1, 2),
            "details": (3, 4),
            "arn": "arn5",
            "called_with": {
                "topic_arn": "arn5",
                "msg": "(3, 4)",
                "subject": "(1, 2)",
            },
        }]
        mock_result = MagicMock()
        for test in tests:
            mock_result.subject = test.get("subject")
            mock_result.details = test.get("details")
            mock_result.disable_notifier = False
            arn = test.get("arn")
            called_with = test.get("called_with")
            notifier_obj = SnsNotifier(mock_result)
            notifier_obj.notify(arn)
            mock_raise.assert_called_with(**called_with)

        # Negative tests)
        negative_arns = [3, 5.5, int, [], {}, ('T', 'uple'), None]
        for arn in negative_arns:
            mock_result.subject, mock_result.details = 'subject', 'details'
            notifier_obj = SnsNotifier(mock_result)
            with self.assertRaises(TypeError):
                notifier_obj.notify(arn)
