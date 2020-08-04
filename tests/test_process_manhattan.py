import unittest
from moto import mock_sns, mock_ecs
from mock import patch

from watchmen import const
from watchmen.process.manhattan import Manhattan

from watchmen.process.manhattan import \
    FEED_URL, \
    MESSAGES, \
    PAGER_TARGET, \
    TARGET


class TestManhattan(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'Type': 'Daily'}
        self.example_event_hourly = {'Type': 'Hourly'}
        self.example_event_weekly = {'Type': 'Weekly'}
        self.example_invalid_events = [
            {'Type': 'hourly'},
            {'Type': 'daily'},
            {'Type': 'weekly'},
            {'type': 'Hourly'},
            {'type': 'Daily'},
            {'type': 'Weekly'},
            {'': ''},
            {}
        ]
        self.example_feed_name = "example_feed"
        self.example_feeds_dict = {
            "Hourly": [
                {
                    "name": "hourly_example",
                    "source_name": "Hourly_Example",
                    "metric_name": "IPV4_TIDE_SUCCESS",
                    "min": 1,
                    "max": 20000,
                    "needs_metric": True
                },
            ],
            "Daily": [
                {
                    "name": "daily_example",
                    "source_name": "Daily_Example",
                    "metric_name": "FQDN_TIDE_SUCCESS",
                    "min": 40000,
                    "max": 300000,
                    "hour_submitted": "11",
                    "needs_metric": True
                },
            ],
            "Weekly": [
                {
                    "name": "weekly_example",
                    "source_name": "Weekly_Example",
                    "metric_name": "FQDN",
                    "min": 250,
                    "max": 450,
                    "hour_submitted": "09",
                    "days_to_subtract": 4,
                    "needs_metric": True
                }
            ]
        }
        self.expected_invalid_event_email_result = {
            'details': MESSAGES.get('exception_invalid_event_message'),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'short_message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'watchman_name': 'Manhattan',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get('exception_invalid_event_subject'),
            'success': False,
            'target': 'Reaper Feeds'
        }
        self.expected_invalid_event_pager_result = {
            'details': MESSAGES.get("exception_message"),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'short_message': MESSAGES.get("exception_message"),
            'result_id': 0,
            'snapshot': {},
            'watchman_name': 'Manhattan',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_invalid_event_subject"),
            'success': False,
            'target': 'Pager Duty'
        }
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
            "short_message": MESSAGES.get("failure_down_message"),
        }
        self.example_exception_summary = {
            "subject": MESSAGES.get("subject_exception_message"),
            "details": self.example_tb_msg,
            "success": None,
            "short_message": MESSAGES.get("exception_message"),
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
                "short_message": MESSAGES.get("failure_down_message"),
                "result_id": 0,
                "snapshot": self.example_snapshot,
                "watchman_name": "Manhattan",
                "state": "FAILURE",
                "subject": self.example_fail_subject,
                "success": False,
                "target": TARGET,
        }
        self.example_pager_result_dict = {
            "details": MESSAGES.get("failure_down_message"),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("failure_down_message"),
            "result_id": 0,
            "snapshot": self.example_snapshot,
            "watchman_name": "Manhattan",
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
            "short_message": MESSAGES.get("exception_message"),
            "result_id": 0,
            "snapshot": {},
            "watchman_name": "Manhattan",
            "state": "EXCEPTION",
            "subject": MESSAGES.get("subject_exception_message"),
            "success": False,
            "target": TARGET,
        }
        self.example_pager_result_dict_ex = {
            "details": MESSAGES.get("exception_message"),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "result_id": 0,
            "snapshot": {},
            "watchman_name": "Manhattan",
            "state": "EXCEPTION",
            "subject": MESSAGES.get("subject_exception_message"),
            "success": False,
            "target": PAGER_TARGET,
        }
        self.example_result_dict_ex = {
            "details": "Manhattan failed due to the following:"
                       "\n\n* when finding bad feed: exception in finding bad feeds!"
                       "\n\n* when finding stuck tasks: exception in finding stuck tasks!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "result_id": 0,
            "snapshot": {},
            "watchman_name": "Manhattan",
            "state": "EXCEPTION",
            "subject": "Manhattan watchmen failed due to an exception!",
            "success": None,
            "target": "Reaper Feeds"
        }
        self.example_json_file = 'json_file'
        self.example_loading_error_msg = 'failed loading'
        self.example_tests = [{
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

    def test_check_invalid_event(self):
        """
        test watchmen.process.manhattan :: Manhattan :: _check_invalid_event
        Testing the method that checks the "event" parameter passed into the Manhattan object is valid.
        """
        # Method should return false whenever the event passed in is valid:
        valid_event_tests = [
            self.example_event_hourly,
            self.example_event_daily,
            self.example_event_weekly
        ]

        for valid_event in valid_event_tests:
            manhattan_obj = Manhattan(event=valid_event, context=None)
            returned = manhattan_obj._check_invalid_event()
            self.assertFalse(returned)

        # Method should return true whenever the event passed in is invalid:
        for invalid_event in self.example_invalid_events:
            manhattan_obj = Manhattan(event=invalid_event, context=None)
            returned = manhattan_obj._check_invalid_event()
            self.assertTrue(returned)

    def test_create_invalid_event_results(self):
        """
        Test watchmen.process.manhattan :: Manhattan :: _create_invalid_event_results
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        returned = manhattan_obj._create_invalid_event_results()

        # The date created and date updated attributes of the result object have to be set manually to properly compare
        # the expected and returned objects:
        email_result = returned[0].to_dict()
        pager_result = returned[1].to_dict()
        email_result["dt_created"] = "2020-12-15T00:00:00+00:00"
        pager_result["dt_created"] = "2020-12-15T00:00:00+00:00"

        # Assert email result returned is correct:
        self.assertEqual(self.expected_invalid_event_email_result, email_result)

        # Assert pager result returned is correct:
        self.assertEqual(self.expected_invalid_event_pager_result, pager_result)

    def test_create_results(self):
        """
        test watchmen.process.manhattan :: Manhattan :: _create_results
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        summary = self.example_summarized_result
        result_dicts = manhattan_obj._create_results(summary, self.example_snapshot)

        email_result = result_dicts[0].to_dict()
        pager_result = result_dicts[1].to_dict()

        # Check the email result
        expected = self.example_result_dict
        # since manhattan does not give observed time, we don't test the time here
        email_result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, email_result)

        # Check the Pager Duty result
        expected = self.example_pager_result_dict
        # since manhattan does not give observed time, we don't test the time here
        pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, pager_result)

    def test_create_results_ex(self):
        """
        test watchmen.model.manhattan :: Manhattan :: _create_results
        Testing exception result
        @return:
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        summary = self.example_exception_summary
        result_dicts = manhattan_obj._create_results(summary, {})

        email_result = result_dicts[0].to_dict()
        pager_result = result_dicts[1].to_dict()

        # Check the email result
        expected = self.example_email_result_dict_ex
        # since manhattan does not give observed time, we don't test the time here
        email_result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(expected, email_result)

        # Check the Pager Duty result
        expected = self.example_pager_result_dict_ex
        # since manhattan does not give observed time, we don't test the time here
        pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"

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

    def test_create_summary(self):
        """
        test watchmen.process.manhattan :: Manhattan :: _create_summary
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)
        event = manhattan_obj.event

        for test in self.example_tests:
            stuck_tasks = test.get("stuck")
            down = test.get("down")
            out_of_range = test.get("oor")
            no_metrics = test.get("no_metrics")

            all_stuck = manhattan_obj._build_bad_tasks_message(stuck_tasks)
            all_down = manhattan_obj._build_bad_tasks_message(down)
            all_range = manhattan_obj._build_bad_tasks_message(out_of_range)
            all_no = manhattan_obj._build_bad_tasks_message(no_metrics)

            # If success, return success information
            subject_line = MESSAGES.get("success_subject").format(event)
            details_body = ""
            success = True
            short_message = MESSAGES.get("success_message")

            # Check for stuck tasks
            if stuck_tasks:
                subject_line = "{} {}{}".format(
                    event,
                    MESSAGES.get("failure_subject"),
                    " | Stuck Tasks"
                )
                details_body = "{}\n\n{}\n\n".format(
                    MESSAGES.get("stuck_tasks_message").format(all_stuck, FEED_URL),
                    const.LINE_SEPARATOR
                )
                short_message = "FAILURE: Stuck Tasks ---- "
                success = False

            # Check if any feeds are down.
            if down:
                if success:
                    subject_line = "{} {}".format(
                        event,
                        MESSAGES.get("failure_subject"),
                    )
                    short_message = "FAILURE: "
                subject_line += ' | Down'
                details_body += '{}{}\n\n{}\n\n'.format(
                    MESSAGES.get("failure_down_message"),
                    all_down,
                    const.LINE_SEPARATOR
                )
                short_message += "Down feeds ---- "
                success = False

            # Check if any feeds are out of threshold range.
            if out_of_range:
                if success:
                    subject_line = "{} {}".format(
                        event,
                        MESSAGES.get("failure_subject"),
                    )
                    short_message = "FAILURE: "
                subject_line += " | Out of Range"
                details_body += '{}{}\n\n{}\n\n'.format(
                    MESSAGES.get("failure_abnormal_message"),
                    all_range,
                    const.LINE_SEPARATOR
                )
                short_message += "Out of range feeds ---- "
                success = False

            # Check if any feeds have no metrics
            if no_metrics:
                if success:
                    subject_line = "{} {}".format(
                        event,
                        MESSAGES.get("failure_subject"),
                    )
                    short_message = "FAILURE: "
                subject_line += ' | No Metrics'
                details_body += "{}".format(MESSAGES.get("no_metrics_message").format(all_no))
                short_message += "Feeds with no metrics ---- "
                success = False

            # If check was not a success, need to add extra line to message for Pager Duty
            if not success:
                short_message += MESSAGES.get("check_email_message")

            expected = {
                "subject": subject_line,
                "details": details_body,
                "success": success,
                'short_message': short_message,
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

    @mock_sns
    @mock_ecs
    @patch('watchmen.process.manhattan.process_feeds_metrics')
    @patch('watchmen.process.manhattan.process_feeds_logs')
    @patch('watchmen.process.manhattan.Manhattan._load_feeds_to_check')
    def test_find_bad_feeds(self, mock_load_feeds, mock_process_logs, mock_process_metrics):
        """
        test watchmen.process.manhattan :: Manhattan :: _find_bad_feeds
        """
        mock_load_feeds.return_value = self.example_feeds_dict, None
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
        expected, expected_tb = (None, None, None), self.example_loading_error_msg
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

    @patch('watchmen.process.manhattan.json.loads')
    @patch('watchmen.process.manhattan.json.load')
    @patch('watchmen.process.manhattan.get_content')
    def test_load_feeds_to_check(self, mock_get_content, mock_load, mock_loads):
        """
        test watchmen.process.manhattan :: Manhattan :: _load_feeds_to_check
        """
        manhattan_obj = Manhattan(event=self.example_event_daily, context=None)

        mock_loads.return_value = self.example_json_file
        expected, expected_msg = self.example_json_file, None
        returned, returned_msg = manhattan_obj._load_feeds_to_check()
        self.assertEqual(expected, returned)
        self.assertEqual(expected_msg, returned_msg)

        # exception occurs
        ex_tests = [TimeoutError, TypeError, Exception, KeyError, ValueError]
        for exception in ex_tests:
            # Make the initial json.load() for the S3 file fail, as well as the nested json.loads() for the local file.
            mock_load.side_effect = exception
            mock_loads.side_effect = exception
            expected, expected_msg = None, exception().__class__.__name__
            returned, returned_msg = manhattan_obj._load_feeds_to_check()
            self.assertEqual(expected, returned)
            self.assertTrue(expected_msg in returned_msg)

    @patch('watchmen.process.manhattan.Manhattan._create_results')
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
