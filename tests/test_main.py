"""
# test_main
"""
from mock import patch
from watchmen import main
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

    def tearDown(self):
        """tearing down at the end of the test"""
        pass

    @patch('watchmen.main.jupiter')
    def test_start_jupiter_watcher(self, mock_jupiter):
        main.start_jupiter_watcher(self.event, self.context)
        mock_jupiter.main.assert_called_once()

    @patch('watchmen.main.manhattan')
    def test_start_manhattan_watcher(self, mock_manhattan):
        main.start_manhattan_watcher(self.event, self.context)
        mock_manhattan.main.assert_called_once()

    @patch('watchmen.main.moloch')
    def test_start_moloch_watcher(self, mock_moloch):
        main.start_moloch_watcher(self.event, self.context)
        mock_moloch.main.assert_called_once()

    @patch('watchmen.main.ozymandias')
    def test_start_ozymandias_watcher(self, mock_ozymandias):
        main.start_ozymandias_watcher(self.event, self.context)
        mock_ozymandias.main.assert_called_once()

    @patch('watchmen.main.rorschach')
    def test_start_rorschach_watcher(self, mock_rorschach):
        main.start_rorschach_watcher(self.event, self.context)
        mock_rorschach.main.assert_called_once()

    @patch('watchmen.main.silhouette')
    def test_start_silhouette_watcher(self, mock_silhouette):
        main.start_silhouette_watcher(self.event, self.context)
        mock_silhouette.main.assert_called_once()

    @patch('watchmen.main.spectre')
    def test_start_spectre_watcher(self, mock_spectre):
        main.start_spectre_watcher(self.event, self.context)
        mock_spectre.main.assert_called_once()
