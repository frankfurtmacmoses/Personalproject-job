import json
import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.endpoints import DATA as LOCAL_ENDPOINTS
from watchmen.process.jupiter import Jupiter
from watchmen.process.jupiter import \
    MESSAGES, \
    TARGET


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.check_time_utc = datetime.utcnow()
        self.example_bad_endpoints_result = {
            "details": MESSAGES.get("not_enough_eps_message"),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("bad_endpoints_message") + const.LINE_SEPARATOR,
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "EXCEPTION",
            "subject": MESSAGES.get("not_enough_eps"),
            "success": False,
            "target": TARGET,
        }
        self.example_data = """[{
                                    "name": "happy data from s3",
                                    "path": "success",
                                    "more": [{
                                        "name": "nested data"
                                    }]
                                },{
                                    "name": "missing data"
                                }]
                                """
        self.example_date_format = '%Y%m%d'
        self.example_empty = {
            "failure": [],
            "success": []
        }
        self.example_endpoints = [
            {"name": "endpoint", "path": "example"},
            {"name": "Used for testing"}
        ]
        self.example_exception_message = "An exception occurred."
        self.example_exception_result = {
            "details": MESSAGES.get("not_enough_eps_message"),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("not_enough_eps_message"),
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "EXCEPTION",
            "subject": MESSAGES.get("not_enough_eps"),
            "success": False,
            "target": TARGET,
        }
        self.example_failed = {
            "failure": [
                {"name": "Failure", "path": "filler/fail", "_err": "something"},
                {"key": "Big fail"}
            ],
            "success": []
        }
        self.example_failure_message = "Endpoints failed during check!"
        self.example_failure_result = {
            "details": self.example_failure_message,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("success_message"),
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": TARGET,
        }
        self.example_holiday_bad_time = datetime(year=2018, month=12, day=25, hour=9, tzinfo=pytz.utc)
        self.example_holiday_good_time = datetime(year=2018, month=12, day=25, hour=8, tzinfo=pytz.utc)
        self.example_holiday_midnight_time = datetime(year=2018, month=12, day=25, hour=0, tzinfo=pytz.utc)
        self.example_invalid_paths = [
            {"key": "that fails"}
        ]
        self.example_no_failures = {
            "failure": [],
            "success": [
                {"name": "succeeded"}
            ]}
        self.example_prefix = "watchmen/jupiter/{}/{}".format(datetime.now().year,
                                                              self.check_time_utc.strftime(self.example_date_format))
        self.example_results_mix = {
            'failure': [{
                'name': 'failed'
            }],
            'success': [{
                'name': 'passed'
            }]}
        self.example_result_parameters = {
            "success": True,
            "disable_notifier": True,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
        }
        self.example_success_result = {
            "details": MESSAGES.get("success_message"),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("success_message"),
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET,
        }
        self.example_valid_paths = [{
            "name": "I will work",
            "path": "here/is/path"
        }]
        self.example_validated = [{
            "name": "endpoint",
            "path": "example"
        }]
        self.example_workday_bad_time = datetime(year=2019, month=10, day=28, hour=15, tzinfo=pytz.utc)
        self.example_workday_good_time = datetime(year=2019, month=10, day=28, hour=12, tzinfo=pytz.utc)
        self.example_weekend_bad_time = datetime(year=2019, month=10, day=27, hour=15, tzinfo=pytz.utc)
        self.example_weekend_good_time = datetime(year=2019, month=10, day=27, hour=16, tzinfo=pytz.utc)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_check_endpoints_path(self, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        tests = [
            {"endpoints": self.example_valid_paths, "expected": self.example_valid_paths},
            {"endpoints": self.example_invalid_paths, "expected": None}
        ]

        for test in tests:
            endpoints = test.get("endpoints")
            expected = test.get("expected")
            returned = jupiter_obj.check_endpoints_path(endpoints)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter._get_time_pdt')
    def test_check_notification_time(self, mock_datetime):
        tests = [
            {"time": self.example_holiday_bad_time, "expected": False},
            {"time": self.example_holiday_good_time, "expected": True},
            {"time": self.example_holiday_midnight_time, "expected": False},
            {"time": self.example_workday_bad_time, "expected": False},
            {"time": self.example_workday_good_time, "expected": True},
            {"time": self.example_weekend_bad_time, "expected": False},
            {"time": self.example_weekend_good_time, "expected": True},
        ]
        for test in tests:
            jupiter_obj = Jupiter(event=None, context=None)
            mock_datetime.return_value = test.get("time")
            expected = test.get("expected")
            returned = jupiter_obj._check_notification_time()
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.Jupiter._check_notification_time')
    @patch('watchmen.process.jupiter.datetime')
    def test_check_skip_notification(self, mock_datetime, mock_time, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)

        success = {
            "failed_nocal_endpoints_msg": "",
            "failed_endpoints_not_using_cal": False,
            "failed_endpoints_using_cal": False,
            "message": "Everything passed",
            "subject": "Happy subject line",
            "success": True,
        }

        failure = {
            "failed_nocal_endpoints_msg": "Message displayed when it is not notification time but there were failed "
                                          "endpoints that do not use the calendar.",
            "failed_endpoints_not_using_cal": True,
            "failed_endpoints_using_cal": False,
            "message": "Contains Failures",
            "subject": "Sad subject line",
            "success": False,
        }

        failure_based_on_notification_time = {
            "failed_nocal_endpoints_msg": "Message displayed when it is not notification time but there were failed "
                                          "endpoints that do not use the calendar.",
            "failed_endpoints_not_using_cal": True,
            "failed_endpoints_using_cal": True,
            "message": "Contains Failures",
            "subject": "Sad subject line",
            "success": False,
        }

        failure_skipped = {
            "failed_nocal_endpoints_msg": "Message displayed when it is not notification time but there were failed "
                                          "endpoints that do not use the calendar.",
            "failed_endpoints_not_using_cal": False,
            "failed_endpoints_using_cal": True,
            "message": "Contains Failures",
            "subject": "Sad subject line",
            "success": False,
        }

        # Cases when the alarm is triggered:
        # - When there are any failed endpoints that do not use the calendar.
        # - When it is notification time and there are any failed endpoints.
        # - When it is not notification time and there are failed endpoints that do not use the calendar.
        failed_endpoints_tests = [{
            "notification_time": False, "summarized_result": failure,
            "expected": failure.get('message'),
        }, {
            "notification_time": True, "summarized_result": failure_based_on_notification_time,
            "expected": failure_based_on_notification_time.get('message'),
        }, {
            "notification_time": False, "summarized_result": failure_based_on_notification_time,
            "expected": failure_based_on_notification_time.get('failed_nocal_endpoints_msg'),
        }]

        # Success is true:
        expected = True, success.get('message')
        returned = jupiter_obj._check_skip_notification_(success)
        self.assertEqual(expected, returned)

        # Testing all scenarios for failed endpoints:
        for test in failed_endpoints_tests:
            mock_time.return_value = test.get("notification_time")
            expected = False, test.get("expected")
            returned = jupiter_obj._check_skip_notification_(test.get("summarized_result"))
            self.assertEqual(expected, returned)

        # Notifications should be skipped when there are only failed endpoints that use the calendar and it is not
        # notification time.
        mock_time.return_value = False
        skip_boolean, skip_message = jupiter_obj._check_skip_notification_(failure_skipped)
        # Cannot mock datetime and return result contains exact time to the second, so just assert that the correct
        # message was returned.
        self.assertIn("Notification is skipped at", skip_message)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_create_invalid_endpoints_result(self, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        expected = self.example_exception_result
        returned = jupiter_obj._create_invalid_endpoints_result().to_dict()
        returned["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned["dt_updated"] = "2018-12-18T00:00:00+00:00"
        self.assertEqual(expected, returned)

    def test_get_result_parameters(self):
        jupiter_obj = Jupiter(event=None, context=None)
        expected = self.example_result_parameters
        returned = jupiter_obj._get_result_parameters(True)
        self.assertEquals(expected, returned)

    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.json.loads')
    @patch('watchmen.process.jupiter.get_content')
    @patch('watchmen.process.jupiter.settings')
    def test_load_endpoints(self, mock_settings, mock_get_content, mock_loads, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        # set default endpoints and content
        mock_get_content.return_value = self.example_data

        # load succeeds
        mock_loads.return_value = self.example_valid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        expected_result = self.example_valid_paths
        returned_result = jupiter_obj.load_endpoints()
        self.assertEqual(expected_result, returned_result)

        # load fails
        mock_loads.side_effect = Exception(self.example_exception_message)
        expected = LOCAL_ENDPOINTS
        returned = jupiter_obj.load_endpoints()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_result(self, mock_dumps, mock_content):
        jupiter_obj = Jupiter(event=None, context=None)
        mock_dumps.return_value = self.example_results_mix
        results = mock_dumps.return_value
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter.load_endpoints')
    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.ServiceChecker')
    @patch('watchmen.process.jupiter.ServiceChecker.start')
    @patch('watchmen.process.jupiter.Jupiter.log_result')
    @patch('watchmen.process.jupiter.ServiceChecker.get_validated_paths')
    @patch('watchmen.process.jupiter.Jupiter.summarize')
    @patch('watchmen.process.jupiter.Jupiter._check_skip_notification_')
    def test_monitor(self, mock_skip_notif, mock_summarize, mock_get_validated_paths, mock_log_result,
                     mock_checker_start, mock_svc_checker, mock_alarm, mock_load_endpoints):
        tests = [
            {"endpoints": self.example_invalid_paths, "expected": self.example_bad_endpoints_result,
             "check_result": None, "details": ""},
            {"endpoints": self.example_valid_paths, "expected": self.example_success_result,
             "check_result": True, "details": MESSAGES.get("success_message")},
            {"endpoints": self.example_valid_paths, "expected": self.example_failure_result,
             "check_result": False, "details": self.example_failure_message}
        ]

        for test in tests:
            jupiter_obj = Jupiter(event=None, context=None)
            endpoints = test.get("endpoints")
            expected = test.get("expected")
            check_result = test.get("check_result")
            details = test.get("details")
            mock_load_endpoints.return_value = endpoints
            mock_skip_notif.return_value = check_result, details
            returned = jupiter_obj.monitor()[0].to_dict()
            returned["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned["dt_updated"] = "2018-12-18T00:00:00+00:00"
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_summarize(self, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        # Failure setup
        failures = self.example_failed.get('failure')

        failed_message = []
        for item in failures:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            failed_message.append(msg)
        failed_message = '{}\n\n\n{}'.format('\n\n'.join(failed_message), MESSAGES.get("check_logs"))

        first_failure = 's' if len(failures) > 1 else ' - {}'.format(failures[0].get('name'))
        failed_subject = '{}{}'.format(MESSAGES.get("error_subject"), first_failure)

        #  Empty results setup
        empty_message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(self.example_empty, sort_keys=True, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_endpoints, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_validated, indent=2)
        )
        empty_message = "{}\n\n\n{}".format(empty_message, MESSAGES.get("no_results"))

        test_results = [{
            "results": self.example_no_failures, "expected": {
                "failed_nocal_endpoints_msg": "", "failed_endpoints_not_using_cal": False,
                "failed_endpoints_using_cal": False, "message": MESSAGES.get("success_message"),
                "subject": MESSAGES.get("success_subject"), "success": True,
            }
        }, {
            "results": self.example_failed, "expected": {
                "failed_nocal_endpoints_msg": failed_message, "failed_endpoints_not_using_cal": True,
                "failed_endpoints_using_cal": False, "message": failed_message, "subject": failed_subject,
                "success": False
            }
        }, {
            "results": self.example_empty, "expected": {
                "failed_nocal_endpoints_msg": "", "failed_endpoints_not_using_cal": False,
                "failed_endpoints_using_cal": False, "message": empty_message, "subject": MESSAGES.get("error_jupiter"),
                "success": False,
            }
        }]

        for test in test_results:
            results = test.get('results')
            expected = test.get('expected')
            returned = jupiter_obj.summarize(results, self.example_endpoints, self.example_validated)
            self.assertEqual(expected, returned)

        # Results DNE
        results = None
        expected = {
            "message": MESSAGES.get("results_dne"), "subject": MESSAGES.get("error_jupiter"), "success": False,
            "failed_nocal_endpoints_msg": "", "failed_endpoints_not_using_cal": False,
            "failed_endpoints_using_cal": False
            }
        returned = jupiter_obj.summarize(results, None, None)
        self.assertEqual(expected, returned)
