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
    def test_start_manhattan_hourly_watcher(self, mock_manhattan_hourly):
        main.start_manhattan_hourly_watcher(self.event, self.context)
        mock_manhattan_hourly.main.assert_called_once()

    @patch('watchmen.main.manhattan_daily')
    def test_start_manhattan_daily_watcher(self, mock_manhattan_daily):
        main.start_manhattan_daily_watcher(self.event, self.context)
        mock_manhattan_daily.main.assert_called_once()

    @patch('watchmen.main.manhattan_weekly')
    def test_start_manhattan_weekly_watcher(self, mock_manhattan_weekly):
        main.start_manhattan_weekly_watcher(self.event, self.context)
        mock_manhattan_weekly.main.assert_called_once()
