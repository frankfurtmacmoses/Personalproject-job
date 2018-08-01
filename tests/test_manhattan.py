import unittest
from mock import patch, MagicMock
from watchmen.manhattan import main, SUCCESS_MESSAGE, FAILURE_MESSAGE, Zeus_Tracker, \
                               tracker_h3x_eu, G01Pack_DGA, ecrimeX, \
                               Xylitol_CyberCrime, cox_feed, bambenek_c2_ip


class TestManhattanWatchmen(unittest.TestCase):

    def setUp(self):
        self.example_empty_list = []
        self.example_failed_list = ['example_feed']
        self.example_exception_message = "Something went wrong"
        self.example_uri_success_metric = {'URI_TIDE_SUCCESS': 'A number'}
        self.example_uri_metric = {'URI': 'A number'}
        self.example_fqdn_success = {'FQDN_TIDE_SUCCESS': 'A number'}
        self.example_ipv4_success = {'IPV4_TIDE_SUCCESS': 'A number'}

    @patch('watchmen.manhattan.Watchmen')
    def test_bambenek_c2_ip(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = bambenek_c2_ip(mock_watchmen, self.example_ipv4_success)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = bambenek_c2_ip(mock_watchmen, self.example_ipv4_success)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_cox_feed(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = cox_feed(mock_watchmen, self.example_ipv4_success)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = cox_feed(mock_watchmen, self.example_ipv4_success)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_xylitol_cybercrime(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = Xylitol_CyberCrime(mock_watchmen, self.example_uri_metric)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = Xylitol_CyberCrime(mock_watchmen, self.example_uri_metric)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_ecrimex(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = ecrimeX(mock_watchmen, self.example_uri_success_metric)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = ecrimeX(mock_watchmen, self.example_uri_success_metric)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_g01_pack_dga(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = G01Pack_DGA(mock_watchmen, self.example_fqdn_success)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = G01Pack_DGA(mock_watchmen, self.example_fqdn_success)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_tracker_h3x_eu(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = tracker_h3x_eu(mock_watchmen, self.example_uri_metric)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = tracker_h3x_eu(mock_watchmen, self.example_uri_metric)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_zeus_tracker(self, mock_watchmen):
        mock_watchmen.check_feed_metric.return_value = False
        expected_result = False
        returned_result = Zeus_Tracker(mock_watchmen, self.example_uri_success_metric)
        self.assertEqual(expected_result, returned_result)
        mock_watchmen.check_feed_metric.return_value = True
        expected_result = True
        returned_result = Zeus_Tracker(mock_watchmen, self.example_uri_success_metric)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.manhattan.Watchmen')
    def test_process_metrics(self, mock_watchmen):
        pass

    @patch('watchmen.manhattan.raise_alarm')
    @patch('watchmen.manhattan.process_feeds_metrics')
    def test_main(self, mock_process_feeds, mock_alarm):
        mock_process_feeds.return_value = self.example_empty_list, self.example_empty_list
        # Test when all feeds are up and running
        expected_result = SUCCESS_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when one of the feeds are down
        mock_process_feeds.return_value = self.example_failed_list, self.example_empty_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when one of the feeds submitted abnormal amounts of domains
        mock_process_feeds.return_value = self.example_empty_list, self.example_failed_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when both a feed is down and a feed submits abnormal amounts of domains
        mock_process_feeds.return_value = self.example_failed_list, self.example_failed_list
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        # Test when exception occurs is processing feeds
        mock_process_feeds.side_effect = Exception(self.example_exception_message)
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
