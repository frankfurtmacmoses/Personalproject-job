from mock import patch
from moto import mock_sns
import unittest

from watchmen.manhattan import main, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'type': 'Daily'}
        self.example_event_hourly = {'type': 'Hourly'}
        self.example_event_weekly = {'type': 'Weekly'}
        self.example_feed_name = "example_feed"
        self.example_exception_msg = "Thingy stopped working"

    @mock_sns
    @patch('watchmen.manhattan.raise_alarm')
    @patch('watchmen.manhattan.Watchmen.get_stuck_ecs_tasks')
    @patch('watchmen.manhattan.Watchmen.process_feeds_metrics')
    @patch('watchmen.manhattan.Watchmen.process_feeds_logs')
    def test_main(self, mock_process_logs, mock_process_feed, mock_get_stuck_tasks, mock_alarm):
        tests = [
            {
                'stuck_tasks': [],
                'downed_feeds': [],
                'abnormal_feeds': [],
                'event': self.example_event_hourly,
                'alarm_call_count': 0,
                'expected': SUCCESS_MESSAGE
            },
            {
                'stuck_tasks': [],
                'downed_feeds': [],
                'abnormal_feeds': [],
                'event': self.example_event_daily,
                'alarm_call_count': 0,
                'expected': SUCCESS_MESSAGE
            },
            {
                'stuck_tasks': [],
                'downed_feeds': [],
                'abnormal_feeds': [],
                'event': self.example_event_weekly,
                'alarm_call_count': 0,
                'expected': SUCCESS_MESSAGE
            },
            {
                'stuck_tasks': ['task_got_stuck'],
                'downed_feeds': [],
                'abnormal_feeds': [],
                'event': self.example_event_hourly,
                'alarm_call_count': 2,
                'expected': FAILURE_MESSAGE
            },
            {
                'stuck_tasks': [],
                'downed_feeds': ['downed_feed'],
                'abnormal_feeds': [],
                'event': self.example_event_hourly,
                'alarm_call_count': 1,
                'expected': FAILURE_MESSAGE
            },
            {
                'stuck_tasks': [],
                'downed_feeds': [],
                'abnormal_feeds': ['submitted_out_of_range_feed'],
                'event': self.example_event_hourly,
                'alarm_call_count': 1,
                'expected': FAILURE_MESSAGE
            },
            {
                'stuck_tasks': [],
                'downed_feeds': ['downed_feed'],
                'abnormal_feeds': ['submitted_out_of_range_feed'],
                'event': self.example_event_hourly,
                'alarm_call_count': 1,
                'expected': FAILURE_MESSAGE
            },
            {
                'stuck_tasks': ['stuck_feed'],
                'downed_feeds': ['downed_feed'],
                'abnormal_feeds': [],
                'event': self.example_event_hourly,
                'alarm_call_count': 3,
                'expected': FAILURE_MESSAGE
            }
        ]
        for test in tests:
            mock_get_stuck_tasks.return_value = test.get('stuck_tasks')
            mock_process_logs.return_value = test.get('downed_feeds')
            mock_process_feed.return_value = test.get('abnormal_feeds')
            result = main(test.get('event'), None)
            self.assertEqual(result, test.get('expected'))
            self.assertEqual(mock_alarm.call_count, test.get('alarm_call_count'))
            mock_alarm.reset_mock()

    @mock_sns
    @patch('watchmen.manhattan.raise_alarm')
    @patch('watchmen.manhattan.Watchmen.get_stuck_ecs_tasks')
    @patch('watchmen.manhattan.Watchmen.process_feeds_metrics')
    @patch('watchmen.manhattan.Watchmen.process_feeds_logs')
    def test_main_exception(self, mock_process_logs, mock_process_feed, mock_get_stuck_tasks, mock_alarm):
        tests = [
            {
                'stuck_tasks': [],
                'downed_feeds': [],
                'abnormal_feeds': [],
                'event': self.example_event_hourly,
                'alarm_call_count': 1,
                'expected': FAILURE_MESSAGE
            }
        ]
        for test in tests:
            mock_process_logs.side_effect = Exception('failure')
            result = main(test.get('event'), None)
            self.assertEqual(result, test.get('expected'))
            mock_alarm.assert_called()
