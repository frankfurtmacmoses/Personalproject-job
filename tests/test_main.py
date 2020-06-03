"""
# test_main
"""
from mock import patch
from watchmen import main
from watchmen import const
from watchmen.common.result import Result
import logging
import unittest


class MainTester(unittest.TestCase):
    """
    MainTester includes all unit tests for main module
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

    @patch('watchmen.process.comedian.Comedian')
    @patch('watchmen.process.comedian.Comedian.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_comedian_watcher(self, mock_alert, mock_monitor, mock_comedian):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_comedian_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.crookshanks.Crookshanks')
    @patch('watchmen.process.crookshanks.Crookshanks.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_crookshanks_watcher(self, mock_alert, mock_monitor, mock_crookshanks):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_crookshanks_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter')
    @patch('watchmen.process.jupiter.Jupiter.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_jupiter_watcher(self, mock_alert, mock_monitor, mock_jupiter):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_jupiter_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.manhattan.Manhattan')
    @patch('watchmen.process.manhattan.Manhattan.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_manhattan_watcher(self, mock_alert, mock_monitor, mock_manhattan):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_manhattan_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.metropolis.Metropolis')
    @patch('watchmen.process.metropolis.Metropolis.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_metropolis_watcher(self, mock_alert, mock_monitor, mock_moloch):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_metropolis_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.moloch.Moloch')
    @patch('watchmen.process.moloch.Moloch.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_moloch_watcher(self, mock_alert, mock_monitor, mock_moloch):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_moloch_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.Mothman')
    @patch('watchmen.process.mothman.Mothman.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_mothman_watcher(self, mock_alert, mock_monitor, mock_mothman):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_mothman_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.silhouette.Silhouette')
    @patch('watchmen.process.silhouette.Silhouette.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_silhouette_watcher(self, mock_alert, mock_monitor, mock_silhouette):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_silhouette_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.slater.Slater')
    @patch('watchmen.process.slater.Slater.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_slater_watcher(self, mock_alert, mock_monitor, mock_slater):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_slater_watcher(self.event, self.context)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.spectre.Spectre')
    @patch('watchmen.process.spectre.Spectre.monitor')
    @patch('watchmen.common.result_svc.ResultSvc.send_alert')
    def test_start_spectre_watcher(self, mock_alert, mock_monitor, mock_spectre):
        mock_monitor.return_value = self.example_result_list

        expected = self.example_lambda_message + const.LINE_SEPARATOR
        returned = main.start_spectre_watcher(self.event, self.context)
        self.assertEqual(expected, returned)
