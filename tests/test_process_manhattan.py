import unittest
from moto import mock_sns, mock_ecs
from mock import patch

from watchmen.models.manhattan import Manhattan

from watchmen.models.manhattan import \
    ABNORMAL_SUBMISSIONS_MESSAGE, \
    ERROR_FEEDS, \
    FAILURE_MESSAGE, \
    FAILURE_SUBJECT, \
    FEED_URL, \
    PAGER_MESSAGE, \
    STUCK_TASKS_MESSAGE, \
    SUBJECT_EXCEPTION_MESSAGE, \
    TARGET


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'type': 'Daily'}
        self.example_event_hourly = {'type': 'Hourly'}
        self.example_event_weekly = {'type': 'Weekly'}
        self.example_feed_name = "example_feed"
        self.example_tb_msg = "Thingy stopped working"
        self.example_stuck_tasks = [{"taskDefinitionArn": "task1"}]
        self.example_found_bad_feeds = (["down_feed"], ["out_of_range"])
        self.example_fail_subject = "Subject Line: Fail"
        self.example_fail_details = "Message Body: things failed\nthis also failed\nEverything keeps failing!"
        self.example_summarized_result = {
            "subject": self.example_fail_subject,
            "details": "Message Body: things failed\nthis also failed\nEverything keeps failing!",
            "success": False,
            "message": PAGER_MESSAGE,
        }
        self.example_exception_summary = {
            "subject": SUBJECT_EXCEPTION_MESSAGE,
            "details": self.example_tb_msg,
            "success": None,
            "message": "NO MESSAGE",
        }
        self.example_notification = "The job was done"
        self.example_watcher_group = "group"
        self.example_down_feeds = ["down1", "down2", "down3", "down4"]
        self.example_out_of_range_feeds = ["oor", "more out of range", "extra out of range"]
        self.example_traceback = "line 4: file\n  error msg\n  more errors  \nError!"
        self.example_snapshot = {
            "down_feeds": self.example_down_feeds,
            "out_of_range_feeds": self.example_out_of_range_feeds,
            "stuck_tasks": self.example_stuck_tasks
        }
        self.example_result_dict = {
                "details": self.example_fail_details,
                "disable_notifier": False,
                "dt_created": "2018-12-18T00:00:00+00:00",
                "dt_updated": "2018-12-18T00:00:00+00:00",
                "is_ack": False,
                "is_notified": False,
                "message": PAGER_MESSAGE,
                "result_id": 0,
                "snapshot": self.example_snapshot,
                "source": "Manhattan",
                "state": "FAILURE",
                "subject": self.example_fail_subject,
                "success": False,
                "target": TARGET,
        }
        self.example_st_tb = "exception in finding stuck tasks!"
        self.example_bf_tb = "exception in finding bad feeds!"
        self.example_result_dict_ex = {
            "details": "Manhattan failed due to the following:"
                       "\n\n* when finding bad feed: exception in finding bad feeds!"
                       "\n\n* when finding stuck tasks: exception in finding stuck tasks!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": {},
            "source": "Manhattan",
            "state": "EXCEPTION",
            "subject": "Manhattan watchmen failed due to an exception!",
            "success": None,
            "target": "Reaper Feeds"
        }

    @mock_sns
    @mock_ecs
    @patch('watchmen.models.manhattan.process_feeds_metrics')
    @patch('watchmen.models.manhattan.process_feeds_logs')
    def test_find_bad_feeds(self, mock_process_logs, mock_process_metrics):
        """
        test watchmen.models.manhattan :: Manhattan :: _find_bad_feeds
        """
        mock_process_logs.return_value = self.example_down_feeds
        mock_process_metrics.return_value = self.example_out_of_range_feeds

        event_types = [self.example_event_hourly,
                       self.example_event_daily,
                       self.example_event_weekly]

        for event in event_types:
            manhattan_obj = Manhattan(event)
            expected = (mock_process_logs(), mock_process_metrics()), None
            returned = manhattan_obj._find_bad_feeds()
            self.assertTupleEqual(expected, returned)

        # Exception finding down feeds and finding out of range feeds
        tests_ex = [mock_process_logs, mock_process_metrics]
        for test in tests_ex:
            test.side_effect = Exception('failure')
            expected_bad_feeds, expected_tb = (None, None), 'failure'
            manhattan_obj = Manhattan(self.example_event_daily)
            bad_feeds, returned_tb = manhattan_obj._find_bad_feeds()
            self.assertEqual(expected_bad_feeds, bad_feeds)
            self.assertTrue(expected_tb in returned_tb)

    @mock_sns
    @patch('watchmen.models.manhattan.get_stuck_ecs_tasks')
    def test_find_stuck_tasks(self, mock_get_stuck):
        """
        test watchmen.models.manhattan :: Manhattan :: _find_stuck_tasks
        """
        manhattan_obj = Manhattan(self.example_event_daily)

        # Everything works well
        mock_get_stuck.return_value = self.example_stuck_tasks
        expected = mock_get_stuck()
        returned, returned_tb = manhattan_obj._find_stuck_tasks()
        self.assertTupleEqual((expected, None), (returned, returned_tb))

        # Exception occurred
        mock_get_stuck.side_effect = Exception('failure')
        expected, expected_tb = None, 'failure'
        returned, returned_tb = manhattan_obj._find_stuck_tasks()
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

    def test_create_summary(self):
        """
        test watchmen.models.manhattan :: Manhattan :: _create_summary
        """
        manhattan_obj = Manhattan(self.example_event_daily)

        tests = [{
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": []
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": []
        }, {
            "stuck": [],
            "down": [],
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds
        }]

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
                all_down += "- {}\n".format(down_feeds)
            for oor in out_of_range:
                all_range += "- {}\n".format(oor)

            subject_line = FAILURE_SUBJECT
            details_body = ""
            message = 'NO MESSAGE'
            success = True
            # Check for stuck tasks
            if stuck_tasks:
                subject_line += ' | Feeds ECS Cluster Has Hung Tasks'
                details_body += STUCK_TASKS_MESSAGE.format(all_stuck, FEED_URL)
                message = PAGER_MESSAGE
                success = False

            # Check if any feeds are down or out of range
            if down or out_of_range:
                subject_line += ' | One or more feeds are down!'
                details_body += "\n{}\n".format('-' * 60) if details_body else ""
                details_body += '{}: {}\n{}\n{}\n{}\n{}\n'.format(
                    self.example_event_daily,
                    FAILURE_MESSAGE,
                    ERROR_FEEDS,
                    all_down,
                    ABNORMAL_SUBMISSIONS_MESSAGE,
                    all_range)
                success = False

            expected = {
                "subject": subject_line,
                "details": details_body,
                "success": success,
                'message': message,
            }
            manhattan_obj.event_type = self.example_event_daily
            returned = manhattan_obj._create_summary(stuck_tasks, (down, out_of_range), None)
            self.assertEqual(expected, returned)

        # If an exception occurred at some point in the process
        stuck = None
        bad = None
        tb = self.example_tb_msg
        expected = self.example_exception_summary
        manhattan_obj.event_type = self.example_exception_summary.get('type')
        returned = manhattan_obj._create_summary(stuck, bad, tb)
        self.assertEqual(expected, returned)

    def test_create_result(self):
        """
        test watchmen.models.manhattan :: Manhattan :: _create_result
        """
        manhattan_obj = Manhattan(self.example_event_daily)
        summary = self.example_summarized_result
        result_dict = manhattan_obj._create_result(summary, self.example_snapshot).to_dict()
        expected = self.example_result_dict

        # since rorschach does not give observed time, we don't test the time here

        result_dict["dt_created"] = "2018-12-18T00:00:00+00:00"
        result_dict["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, result_dict)

    def test_create_snapshot(self):
        """
        test watchmen.models.manhattan :: Manhattan :: _create_snapshot
        """
        manhattan_obj = Manhattan(self.example_event_daily)
        tests = [{
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": []
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": []
        }, {
            "stuck": [],
            "down": [],
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds
        }]
        for test in tests:
            stucks = test.get("stuck")
            down = test.get("down")
            oor = test.get("oor")
            expected = {}
            if down:
                expected["down_feeds"] = down
            if oor:
                expected["out_of_range_feeds"] = oor
            if stucks:
                expected["stuck_tasks"] = []
                for stuck in stucks:
                    expected.get("stuck_tasks").append(stuck.get("taskDefinitionArn"))
            result = manhattan_obj._create_snapshot(stucks, (down, oor))
            self.assertEqual(expected, result)

    @patch('watchmen.models.manhattan.Manhattan._create_summary')
    @patch('watchmen.models.manhattan.Manhattan._create_snapshot')
    def test_monitor(self, mock_snapshot, mock_summary):
        """
        test watchmen.model.manhattan :: Manhattan :: monitor
        """
        manhattan_obj = Manhattan(self.example_event_daily)
        mock_summary.return_value = self.example_summarized_result
        mock_snapshot.return_value = self.example_snapshot
        expected = self.example_result_dict
        result = manhattan_obj.monitor()[0].to_dict()

        # since rorschach does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"
        result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, result)

    @patch('watchmen.models.manhattan.Manhattan._find_stuck_tasks')
    @patch('watchmen.models.manhattan.Manhattan._find_bad_feeds')
    def test_monitor_ex(self, mock_bad_feeds, mock_stuck_tasks):
        """
        test watchmen.model.manhattan :: Manhattan :: monitor
        Testing exceptions
        @return:
        """
        manhattan_obj = Manhattan(self.example_event_daily)
        mock_bad_feeds.return_value = None, self.example_bf_tb
        mock_stuck_tasks.return_value = None, self.example_st_tb
        expected = self.example_result_dict_ex
        result = manhattan_obj.monitor()[0].to_dict()

        # since rorschach does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"
        result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, result)
