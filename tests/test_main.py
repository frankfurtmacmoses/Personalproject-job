import unittest
from watchmen import main
from mock import patch


class TestMain(unittest.TestCase):

    def setUp(self):
        self.event = {}
        self.context = {}

    @patch('watchmen.main.moloch')
    def test_start_moloch_watcher(self, mock_moloch):
        main.start_moloch_watcher(self.event, self.context)
        mock_moloch.main.assert_called_once()

    @patch('watchmen.main.silhouette')
    def test_start_silhouette_watcher(self, mock_silhouette):
        main.start_silhouette_watcher(self.event, self.context)
        mock_silhouette.main.assert_called_once()

    @patch('watchmen.main.manhattan_hourly')
    def test_start_manhattan_hourly_watcher(self, mock_manhattan):
        main.start_manhattan_hourly_watcher(self.event, self.context)
        mock_manhattan.main.assert_called_once()
