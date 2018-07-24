import unittest
from watchmen import main
from mock import patch


class TestMain(unittest.TestCase):

    @patch('watchmen.main.moloch')
    def test_start_moloch_watcher(self, mock_moloch):
        main.start_moloch_watcher()
        mock_moloch.main.assert_called_once()

    @patch('watchmen.main.silhouette')
    def test_start_silhouette_watcher(self, mock_silhouette):
        main.start_silhouette_watcher()
        mock_silhouette.main.assert_called_once()
