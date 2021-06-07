"""
# test_main
"""
from mock import patch
from watchmen import const
from watchmen.common.result import Result
from watchmen import main_atg as main
import logging
import unittest


class MainAtgTester(unittest.TestCase):
    """
    MainAtgTester includes all unit tests for main module
    """

    @classmethod
    def teardown_class(cls):
        logging.shutdown()

    def setUp(self):
        """setup for test"""
        self.event = {}
        self.context = {}

        self.example_lambda_message = "Messages that are in the list of results."
        self.example_result_list = [Result(
            short_message=self.example_lambda_message,
            success=True,
            state="SUCCESS",
            subject="Success subject.",
            watchman_name="Example source",
            target="Fake target",
        )]

    @patch('watchmen.process.bernard.Bernard')
    @patch('watchmen.process.bernard.Bernard.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_bernard_watcher(self, mock_alert, mock_save, mock_monitor, mock_bernard):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_bernard_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.Comedian')
    @patch('watchmen.process.comedian.Comedian.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_comedian_watcher(self, mock_alert, mock_save, mock_monitor, mock_comedian):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_comedian_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter')
    @patch('watchmen.process.jupiter.Jupiter.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_jupiter_watcher(self, mock_alert, mock_save, mock_monitor, mock_jupiter):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_jupiter_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.manhattan.Manhattan')
    @patch('watchmen.process.manhattan.Manhattan.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_manhattan_watcher(self, mock_alert, mock_save, mock_monitor, mock_manhattan):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_manhattan_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.Metropolis')
    @patch('watchmen.process.metropolis.Metropolis.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_metropolis_watcher(self, mock_alert, mock_save, mock_monitor, mock_metropolis):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_metropolis_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.Mothman')
    @patch('watchmen.process.mothman.Mothman.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_mothman_watcher(self, mock_alert, mock_save, mock_monitor, mock_mothman):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_mothman_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.silhouette.Silhouette')
    @patch('watchmen.process.silhouette.Silhouette.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.save_results')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_silhouette_watcher(self, mock_alert, mock_save, mock_monitor, mock_silhouette):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_silhouette_watcher(self.event, self.context)
        self.assertEqual(expected, returned)
