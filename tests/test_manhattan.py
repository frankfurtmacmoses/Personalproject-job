from mock import patch
from moto import mock_sns, mock_ecs
import unittest

from watchmen.process.manhattan import \
    ABNORMAL_SUBMISSIONS_MESSAGE, \
    ERROR_FEEDS, \
    EXCEPTION_MESSAGE, \
    FAILURE_MESSAGE, \
    FEED_URL, \
    PAGER_MESSAGE, \
    STUCK_TASKS_MESSAGE, \
    SUBJECT_MESSAGE, \
    SUCCESS_MESSAGE
from watchmen.process.manhattan import find_bad_feeds, find_stuck_tasks, main, notify, summarize


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'type': 'Daily'}
        self.example_event_hourly = {'type': 'Hourly'}
        self.example_event_weekly = {'type': 'Weekly'}
        self.example_feed_name = "example_feed"
        self.example_exception_msg = "Thingy stopped working"
        self.example_stuck_tasks = ["task1", "task2"]
        self.example_found_bad_feeds = (["down_feed"], ["out_of_range"])
        self.example_summarized_result = {
            "subject": "Subject Line: Fail",
            "message": "Message Body: things failed\nthis also failed\nEverything keeps failing!",
            "success": False,
            "pager_message": PAGER_MESSAGE,
        }
        self.example_notification = "The job was done"
        self.example_watcher_group = "group"
        self.example_down_feeds = ["down1", "down2", "down3", "down4"]
        self.example_out_of_range_feeds = ["oor", "more out of range", "extra out of range"]
        self.example_traceback = "line 4: file\n  error msg\n  more errors  \nError!"

    @mock_sns
    @mock_ecs
    @patch('watchmen.process.manhattan.raise_alarm')
    @patch('watchmen.process.manhattan.process_feeds_metrics')
    @patch('watchmen.process.manhattan.process_feeds_logs')
    def test_find_bad_feeds(self, mock_process_logs, mock_process_metrics, mock_alarm):
        mock_process_logs.return_value = self.example_down_feeds
        mock_process_metrics.return_value = self.example_out_of_range_feeds

        event_types = [self.example_event_hourly.get("type"),
                       self.example_event_daily.get("type"),
                       self.example_event_weekly.get("type")]

        for event in event_types:
            expected = mock_process_logs(), mock_process_metrics()
            returned = find_bad_feeds(event)
            self.assertEqual(expected, returned)

        # Exception finding down feeds
        mock_process_logs.side_effect = Exception('failure')
        expected = None
        returned = find_bad_feeds("Daily")
        self.assertEqual(expected, returned)

        # Exception finding out of range feeds
        mock_process_metrics.side_effect = Exception('failure')
        expected = None
        returned = find_bad_feeds("Daily")
        self.assertEqual(expected, returned)

    @mock_sns
    @patch('watchmen.process.manhattan.raise_alarm')
    @patch('watchmen.process.manhattan.get_stuck_ecs_tasks')
    def test_find_stuck_tasks(self, mock_get_stuck, mock_alarm):

        # Everything works well
        mock_get_stuck.return_value = self.example_stuck_tasks
        expected = mock_get_stuck()
        returned = find_stuck_tasks()
        self.assertEqual(expected, returned)

        # Exception occurred
        mock_get_stuck.side_effect = Exception('failure')
        expected = None
        returned = find_stuck_tasks()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.manhattan.notify')
    @patch('watchmen.process.manhattan.summarize')
    @patch('watchmen.process.manhattan.find_bad_feeds')
    @patch('watchmen.process.manhattan.find_stuck_tasks')
    def test_main(self, mock_find_stuck, mock_find_bad, mock_summarize, mock_notify):
        # Check for stuck tasks
        mock_find_stuck.return_value = self.example_stuck_tasks
        stuck = mock_find_stuck()
        self.assertIsNotNone(stuck)
        mock_find_stuck.assert_called_with()
        # Check for down or out of range feeds
        mock_find_bad.return_value = self.example_found_bad_feeds
        bad = mock_find_bad()
        self.assertIsNotNone(bad)
        mock_find_bad.assert_called_with()
        #  Summarize the results
        mock_summarize.return_value = self.example_summarized_result
        summarized_results = mock_summarize()
        self.assertIsNotNone(summarized_results)
        mock_summarize.assert_called_with()
        # Send alarm notification and return status of the feeds
        mock_notify.return_value = self.example_notification
        notification = mock_notify()
        self.assertIsNotNone(notification)
        mock_notify.assert_called_with()
        # Check if a notification is returned
        expected = notification
        returned = main(self.example_event_hourly, None)
        self.assertEqual(expected, returned)

    @mock_sns
    @patch('watchmen.process.manhattan.raise_alarm')
    def test_notify(self, mock_alarm):
        bad_result = self.example_summarized_result
        good_result = {
            "subject": "Subject Line: Pass",
            "message": "Message Body: Good Stuff",
            "success": True,
            "pager_message": PAGER_MESSAGE,
        }

        # Exception occurred
        expected = "Failure: an exception occurred during checking process.\n{}".format(EXCEPTION_MESSAGE)
        returned = notify(None)
        self.assertEqual(expected, returned)

        # Failure
        expected = FAILURE_MESSAGE
        returned = notify(bad_result)
        self.assertEqual(expected, returned)

        # Success
        expected = SUCCESS_MESSAGE
        returned = notify(good_result)
        self.assertEqual(expected, returned)

    def test_summarize(self):
        tests = [
            {"stuck": self.example_stuck_tasks, "down": [], "oor": []},
            {"stuck": [], "down": self.example_down_feeds, "oor": []},
            {"stuck": [], "down": [], "oor": self.example_out_of_range_feeds},
            {"stuck": self.example_stuck_tasks, "down": self.example_down_feeds, "oor": []},
            {"stuck": self.example_stuck_tasks, "down": [], "oor": self.example_out_of_range_feeds},
            {"stuck": [], "down": self.example_down_feeds, "oor": self.example_out_of_range_feeds},
            {"stuck": self.example_stuck_tasks, "down": self.example_down_feeds, "oor": self.example_out_of_range_feeds}
        ]

        for test in tests:
            stuck_tasks = test.get("stuck")
            down = test.get("down")
            out_of_range = test.get("oor")

            all_stuck = ""
            all_down = ""
            all_range = ""
            for stuck in stuck_tasks:
                all_stuck += "{}\n".format(stuck)
            for down_feeds in down:
                all_down += "{}\n".format(down_feeds)
            for oor in out_of_range:
                all_range += "{}\n".format(oor)

            subject_line = SUBJECT_MESSAGE
            message_body = ""
            pager_message = ""
            success = True
            # Check for stuck tasks
            if stuck_tasks:
                subject_line += ' | Feeds ECS Cluster Has Hung Tasks'
                message_body += STUCK_TASKS_MESSAGE.format(all_stuck, FEED_URL)
                pager_message = PAGER_MESSAGE
                success = False

            # Check if any feeds are down or out of range
            if down or out_of_range:
                subject_line += ' | One or more feeds are down!'
                message_body += "\n\n\n{}\n".format('-' * 60) if message_body else ""
                message_body += '{}: {}\n{}\n{}\n{}\n{}\n'.format(
                    self.example_event_daily.get('type'),
                    FAILURE_MESSAGE,
                    ERROR_FEEDS,
                    all_down,
                    ABNORMAL_SUBMISSIONS_MESSAGE,
                    all_range)
                success = False

            expected = {
                "subject": subject_line,
                "message": message_body,
                "success": success,
                "pager_message": pager_message,
            }
            returned = summarize(self.example_event_daily.get("type"), stuck_tasks, (down, out_of_range))
            self.assertEqual(expected, returned)

        # If an exception occurred at some point in the process
        stuck = None
        bad = None
        expected = None
        returned = summarize(self.example_event_daily.get("type"), stuck, bad)
        self.assertEqual(expected, returned)
