import unittest
from moto import mock_sns, mock_ecs
from mock import patch

from watchmen.process.manhattan import Manhattan

from watchmen.process.manhattan import \
    ABNORMAL_SUBMISSIONS_MESSAGE, \
    CHECK_EMAIL_MESSAGE, \
    ERROR_FEEDS, \
    EXCEPTION_MESSAGE, \
    FAILURE_MESSAGE, \
    FAILURE_SUBJECT, \
    FEED_URL, \
    NO_METRICS_MESSAGE, \
    STUCK_TASKS_MESSAGE, \
    SUBJECT_EXCEPTION_MESSAGE, \
    SUCCESS_SUBJECT, \
    SUCCESS_MESSAGE, \
    PAGER_TARGET, \
    TARGET


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'Type': 'Daily'}
        self.example_event_hourly = {'Type': 'Hourly'}
        self.example_event_weekly = {'Type': 'Weekly'}
        self.example_feed_name = "example_feed"
        self.example_tb_msg = "Thingy stopped working"
        self.example_stuck_tasks = [{"taskDefinitionArn": "task1"}]
        self.example_found_bad_feeds = (["down_feed"], ["out_of_range"], ["no_metrics"])
        self.example_stuck_tasks_with_tb = [{"taskDefinitionArn": "task1"}], None
        self.example_found_bad_feeds_with_tb = (["down_feed"], ["out_of_range"], ["no_metrics"]), None
        self.example_fail_subject = "Subject Line: Fail"
        self.example_fail_details = "Message Body: things failed\nthis also failed\nEverything keeps failing!"
        self.example_summarized_result = {
            "subject": self.example_fail_subject,
            "details": "Message Body: things failed\nthis also failed\nEverything keeps failing!",
            "success": False,
            "message": FAILURE_MESSAGE,
        }
        self.example_exception_summary = {
            "subject": SUBJECT_EXCEPTION_MESSAGE,
            "details": self.example_tb_msg,
            "success": None,
            "message": EXCEPTION_MESSAGE,
        }
        self.example_notification = "The job was done"
        self.example_watcher_group = "group"
        self.example_down_feeds = ["down1", "down2", "down3", "down4"]
        self.example_out_of_range_feeds = ["oor", "more out of range", "extra out of range"]
        self.example_no_metrics_feeds = ['Nothing1', 'Nothing2']
        self.example_traceback = "line 4: file\n  error msg\n  more errors  \nError!"
        self.example_snapshot = {
            "down_feeds": self.example_down_feeds,
            "out_of_range_feeds": self.example_out_of_range_feeds,
            "stuck_tasks": self.example_stuck_tasks,
            "no_metrics_feeds": self.example_no_metrics_feeds
        }
        self.example_result_dict = {
                "details": self.example_fail_details,
                "disable_notifier": False,
                "dt_created": "2018-12-18T00:00:00+00:00",
                "dt_updated": "2018-12-18T00:00:00+00:00",
                "is_ack": False,
                "is_notified": False,
                "message": FAILURE_MESSAGE,
                "result_id": 0,
                "snapshot": self.example_snapshot,
                "source": "Manhattan",
                "state": "FAILURE",
                "subject": self.example_fail_subject,
                "success": False,
                "target": TARGET,
        }
        self.example_pager_result_dict = {
            "details": FAILURE_MESSAGE,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": FAILURE_MESSAGE,
            "result_id": 0,
            "snapshot": self.example_snapshot,
            "source": "Manhattan",
            "state": "FAILURE",
            "subject": self.example_fail_subject,
            "success": False,
            "target": PAGER_TARGET,
        }
        self.example_st_tb = "exception in finding stuck tasks!"
        self.example_bf_tb = "exception in finding bad feeds!"
        self.example_email_result_dict_ex = {
            "details": self.example_tb_msg,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": EXCEPTION_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Manhattan",
            "state": "EXCEPTION",
            "subject": SUBJECT_EXCEPTION_MESSAGE,
            "success": None,
            "target": TARGET,
        }
        self.example_pager_result_dict_ex = {
            "details": EXCEPTION_MESSAGE,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": EXCEPTION_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Manhattan",
            "state": "EXCEPTION",
            "subject": SUBJECT_EXCEPTION_MESSAGE,
            "success": None,
            "target": PAGER_TARGET,
        }
        self.example_result_dict_ex = {
            "details": "Manhattan failed due to the following:"
                       "\n\n* when finding bad feed: exception in finding bad feeds!"
                       "\n\n* when finding stuck tasks: exception in finding stuck tasks!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": EXCEPTION_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Manhattan",
            "state": "EXCEPTION",
            "subject": "Manhattan watchmen failed due to an exception!",
            "success": None,
            "target": "Reaper Feeds"
        }
        self.example_json_file = 'json_file'
        self.example_loading_error_msg = 'failed loading'

    @mock_sns
    @mock_ecs
    @patch('watchmen.process.manhattan.process_feeds_metrics')
    @patch('watchmen.process.manhattan.process_feeds_logs')
    def test_find_bad_feeds(self, mock_process_logs, mock_process_metrics):
        """
        test watchmen.process.manhattan :: Manhattan :: _find_bad_feeds
        """
        mock_process_logs.return_value = self.example_down_feeds
        mock_process_metrics.return_value = self.example_out_of_range_feeds, self.example_no_metrics_feeds

        event_types = [self.example_event_hourly,
                       self.example_event_daily,
                       self.example_event_weekly]

        for event in event_types:
            manhattan_obj = Manhattan(event=event, context=None)
            mock_oor, mock_no_met = mock_process_metrics()
            expected = (mock_process_logs(), mock_oor, mock_no_met), None
            returned = manhattan_obj._find_bad_feeds()
            self.assertTupleEqual(expected, returned)

        # Exception finding down feeds and finding out of range feeds
        tests_ex = [mock_process_logs, mock_process_metrics]
        for test in tests_ex:
            test.side_effect = Exception('failure')
            expected_bad_feeds, expected_tb = (None, None), 'failure'
            manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
            bad_feeds, returned_tb = manhattan_obj._find_bad_feeds()
            self.assertEqual(expected_bad_feeds, bad_feeds)
            self.assertTrue(expected_tb in returned_tb)

    @patch('watchmen.process.manhattan.Manhattan._load_feeds_to_check')
    def test_find_bad_feeds_fails_loading(self, mock_load_feeds):
        """
        test watchmen.process.manhattan :: Manhattan :: _find_bad_feeds
        test when load feeds returns nothing
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        mock_load_feeds.return_value = None, self.example_loading_error_msg
        expected, expected_tb = (None, None), self.example_loading_error_msg
        returned, returned_tb = manhattan_obj._find_bad_feeds()
        self.assertEqual(expected, returned)
        self.assertEqual(expected_tb, returned_tb)

    @mock_sns
    @patch('watchmen.process.manhattan.get_stuck_ecs_tasks')
    def test_find_stuck_tasks(self, mock_get_stuck):
        """
        test watchmen.process.manhattan :: Manhattan :: _find_stuck_tasks
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)

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
        test watchmen.process.manhattan :: Manhattan :: _create_summary
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        event = manhattan_obj.event

        tests = [{
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": [],
            "down": [],
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": [],
            "down": [],
            "oor": [],
            "no_metrics": self.example_no_metrics_feeds
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": [self.example_stuck_tasks],
            "down": [],
            "oor": [],
            "no_metrics": self.example_no_metrics_feeds
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": self.example_no_metrics_feeds
        }]

        for test in tests:
            stuck_tasks = test.get("stuck")
            down = test.get("down")
            out_of_range = test.get("oor")
            no_metrics = test.get("no_metrics")

            all_stuck = ""
            all_down = ""
            all_range = ""
            all_no = ""

            for stuck in stuck_tasks:
                all_stuck += "{}\n".format(stuck)
            for down_feeds in down:
                all_down += "- {}\n".format(down_feeds)
            for oor in out_of_range:
                all_range += "- {}\n".format(oor)
            for no_met in no_metrics:
                all_no += "{}\n".format(no_met)

            # set subject line to success first
            subject_line = SUCCESS_SUBJECT.format(event)
            details_body = ""
            success = True
            message = SUCCESS_MESSAGE
            # Check for stuck tasks
            if stuck_tasks:
                subject_line = FAILURE_SUBJECT + ' | Feeds ECS Cluster Has Hung Tasks'
                details_body += STUCK_TASKS_MESSAGE.format(all_stuck, FEED_URL)
                message = "FAILURE: Stuck Tasks"
                success = False

            # Check if any feeds are down or out of range
            if down or out_of_range:
                if success:
                    subject_line = FAILURE_SUBJECT
                    message = "FAILURE: "
                subject_line += ' | One or more feeds are down!'
                details_body += "\n{}\n".format('-' * 60) if details_body else ""
                details_body += '{}: {}\n{}\n{}\n{}\n{}\n'.format(
                    event,
                    FAILURE_MESSAGE,
                    ERROR_FEEDS,
                    all_down,
                    ABNORMAL_SUBMISSIONS_MESSAGE,
                    all_range)
                message += "- Down or Out of Range feeds"
                success = False

            # Check if any feeds have no metrics
            if no_metrics:
                if success:
                    subject_line = FAILURE_SUBJECT
                    message = "FAILURE: "
                subject_line += ' | One or more feeds have NO metrics!'
                details_body += "\n\n\n{}\n".format('-' * 60) if details_body else ""
                details_body += NO_METRICS_MESSAGE.format(all_no)
                message += "- Feeds with no metrics"
                success = False

            if not success:
                message += CHECK_EMAIL_MESSAGE

            expected = {
                "subject": subject_line,
                "details": details_body,
                "success": success,
                'message': message,
            }
            returned = manhattan_obj._create_summary(stuck_tasks, (down, out_of_range, no_metrics), None)
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
        test watchmen.process.manhattan :: Manhattan :: _create_result
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        summary = self.example_summarized_result
        result_dicts = manhattan_obj._create_result(summary, self.example_snapshot)

        email_result = result_dicts[0].to_dict()
        pager_result = result_dicts[1].to_dict()

        # Check the email result
        expected = self.example_result_dict
        # since manhattan does not give observed time, we don't test the time here
        email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        email_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, email_result)

        # Check the Pager Duty result
        expected = self.example_pager_result_dict
        # since manhattan does not give observed time, we don't test the time here
        pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        pager_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, pager_result)

    def test_create_result_ex(self):
        """
        test watchmen.model.manhattan :: Manhattan :: _create_result
        Testing exception result
        @return:
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        summary = self.example_exception_summary
        result_dicts = manhattan_obj._create_result(summary, {})

        email_result = result_dicts[0].to_dict()
        pager_result = result_dicts[1].to_dict()

        # Check the email result
        expected = self.example_email_result_dict_ex
        # since manhattan does not give observed time, we don't test the time here
        email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        email_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, email_result)

        # Check the Pager Duty result
        expected = self.example_pager_result_dict_ex
        # since manhattan does not give observed time, we don't test the time here
        pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        pager_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, pager_result)

    def test_create_snapshot(self):
        """
        test watchmen.process.manhattan :: Manhattan :: _create_snapshot
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        tests = [{
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": [],
            "down": [],
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": [],
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": [],
            "no_metrics": [self.example_no_metrics_feeds]
        }, {
            "stuck": self.example_stuck_tasks,
            "down": [],
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": [],
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": []
        }, {
            "stuck": self.example_stuck_tasks,
            "down": self.example_down_feeds,
            "oor": self.example_out_of_range_feeds,
            "no_metrics": self.example_no_metrics_feeds
        }]
        for test in tests:
            stucks = test.get("stuck")
            down = test.get("down")
            oor = test.get("oor")
            no_metrics = test.get("no_metrics")
            expected = {}
            if down:
                expected["down_feeds"] = down
            if oor:
                expected["out_of_range_feeds"] = oor
            if no_metrics:
                expected["no_metrics_feeds"] = no_metrics
            if stucks:
                print("LOOK HERE: {}".format(stucks))
                expected["stuck_tasks"] = []
                for stuck in stucks:
                    expected.get("stuck_tasks").append(stuck.get("taskDefinitionArn"))
            result = manhattan_obj._create_snapshot(stucks, (down, oor, no_metrics))
            self.assertEqual(expected, result)

    @patch('watchmen.process.manhattan.json.load')
    def test_load_feeds_to_check(self, mock_load):
        """
        test watchmen.process.manhattan :: Manhattan :: _load_feeds_to_check
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)

        mock_load.return_value = self.example_json_file
        expected, expected_msg = self.example_json_file, None
        returned, returned_msg = manhattan_obj._load_feeds_to_check()
        self.assertEqual(expected, returned)
        self.assertEqual(expected_msg, returned_msg)

        # exception occurs
        ex_tests = [TimeoutError, TypeError, Exception, KeyError, ValueError]
        for exception in ex_tests:
            mock_load.side_effect = exception
            expected, expected_msg = None, exception().__class__.__name__
            returned, returned_msg = manhattan_obj._load_feeds_to_check()
            self.assertEqual(expected, returned)
            self.assertTrue(expected_msg in returned_msg)

    @patch('watchmen.process.manhattan.Manhattan._create_result')
    @patch('watchmen.process.manhattan.Manhattan._create_summary')
    @patch('watchmen.process.manhattan.Manhattan._create_tb_details')
    @patch('watchmen.process.manhattan.Manhattan._create_snapshot')
    @patch('watchmen.process.manhattan.Manhattan._find_bad_feeds')
    @patch('watchmen.process.manhattan.Manhattan._find_stuck_tasks')
    def test_monitor(self, mock_stuck, mock_bad, mock_snapshot, mock_tb_details, mock_summary, mock_result):
        """
        test watchmen.model.manhattan :: Manhattan :: monitor
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        mock_stuck.return_value = self.example_stuck_tasks_with_tb
        mock_bad.return_value = self.example_found_bad_feeds_with_tb
        mock_snapshot.return_value = self.example_snapshot
        mock_tb_details.return_value = self.example_tb_msg
        mock_summary.return_value = self.example_summarized_result
        mock_result.return_value = [self.example_result_dict, self.example_pager_result_dict]

        expected = mock_result()
        returned = manhattan_obj.monitor()
        self.assertEqual(expected, returned)
