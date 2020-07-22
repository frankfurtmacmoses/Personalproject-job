"""
# test_main_rorschach
"""
import unittest
from mock import patch
from watchmen import const, main_rorschach
from watchmen.common.result import Result


class MainRorschachTester(unittest.TestCase):
    """
    MainRorschachTester tests main_rorschach.py
    """

    @patch('watchmen.process.rorschach.Rorschach')
    @patch('watchmen.process.rorschach.Rorschach.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_rorschach_watcher(self, mock_alert, mock_monitor, mock_rorschach):
        example_lambda_message = "Messages that are in the list of results."
        mock_monitor.return_value = [Result(
            short_message=example_lambda_message,
            state="SUCCESS",
            subject="Success subject.",
            success=True,
            target="Fake target",
            watchman_name="Example source",
        )]

        expected = example_lambda_message + const.LINE_SEPARATOR
        returned = main_rorschach.start_rorschach_watcher({}, None)
        self.assertEqual(expected, returned)
