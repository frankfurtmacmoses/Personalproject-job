import json
import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.endpoints import DATA as LOCAL_ENDPOINTS
from watchmen.process.jupiter import Jupiter


class TestJupiter(unittest.TestCase):

    def setUp(self):
        # Messages
        self.check_logs = "Please check logs for more details!"
        self.check_time_utc = datetime.utcnow()
        self.error_jupiter = "Jupiter: Failure in runtime"
        self.error_subject = "Jupiter: Failure in checking endpoint"
        self.no_results = "There are no results! Endpoint file might be empty or Service Checker may not be working" \
                          " correctly. Please check logs and endpoint file to help identify the issue."
        self.results_dne = "Results do not exist! There is nothing to check. Service Checker may not be working " \
                           "correctly. Please check logs and endpoint file to help identify the issue."
        self.success_message = "All endpoints are healthy!"
        self.success_subject = "Jupiter: Cyber Intel endpoints are working properly!"
        self.s3_fail_load_message = "Cannot load endpoints from the following S3 resource:"

        self.example_bad_list = [
            {"name": "NoPath"},
            {}
        ]
        self.example_bad_messages = "There is not a path to check for: HaveName\n" \
                                    "There is not a path to check for: There is not a name available"
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
        self.example_exception_message = "Something failed"
        self.example_failed = {
            "failure": [
                {"name": "Failure", "path": "filler/fail", "_err": "something"},
                {"key": "Big fail"}
            ],
            "success": []
        }
        self.example_few_validated = []
        self.example_invalid_paths = [
            {"key": "that fails"}
        ]
        self.example_local_endpoints = [
            {"name": "local", "path": "s3/failed"}
        ]
        self.example_validated_list = [
            {"name": "HaveName", "path": "have/path"},
            {"path": "pathWith/NoName"}
        ]
        self.example_no_failures = {
            "failure": [],
            "success": [
                {"name": "succeeded"}
            ]}
        self.example_passed_endpoints = [
            {"name": "good endpoint", "path": "good/path"}
        ]
        self.example_prefix = "watchmen/jupiter/{}/{}".format("2019",
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
            "subject": self.success_subject,
        }
        self.example_results_passed = {
            'failure': [{
                'name': 'failed'
            }],
            'success': [{
                'name': 'passed'
            }]}
        self.example_status = "Everything has been checked!"
        self.example_summarized_results = {
            "last_failed": True,
            "message": "This is your in-depth result",
            "subject": "Good subject line",
            "success": False,
        }
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_valid_paths = [{
            "name": "I will work",
            "path": "here/is/path"
        }]
        self.example_validated = [{
            "name": "endpoint",
            "path": "example"
        }]
        self.example_variety_endpoints = [
            {"name": "endpoint", "path": "cool/path"},
            {"key": "bad endpoint"}
        ]

    @patch('watchmen.process.jupiter.get_content')
    def test_check_last_failure(self, mock_get_content):
        jupiter_obj = Jupiter(event=None, context=None)
        test_results = [
            {"file_content": None, "expected": False},
            {"file_content": "", "expected": False},
            {"file_content": "FAILURE!!!", "expected": True}
        ]

        for test in test_results:
            mock_get_content.return_value = test.get("file_content")
            expected = test.get("expected")
            returned = jupiter_obj._check_last_failure()
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.get_boolean')
    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.Jupiter._check_last_failure')
    @patch('watchmen.process.jupiter.Jupiter._check_time')
    @patch('watchmen.process.jupiter.datetime')
    def test_check_skip_notification(self, mock_datetime, mock_time, mock_last_fail, mock_alarm, mock_boolean):
        jupiter_obj = Jupiter(event=None, context=None)
        success = {
            "last_failed": False,
            "message": "Everything passed",
            "subject": "Happy subject line",
            "success": True,
        }

        failure = {
            "message": "Contains Failures",
            "subject": "Sad subject line",
            "success": False,
        }

        skip_tests = [{
            "use_cal": False, "last_failed": True, "skip": False,
            "expected": failure.get('message'),
        }, {
            "use_cal": True, "last_failed": False, "skip": False,
            "expected": failure.get('message'),
        }, {
            "use_cal": True, "last_failed": True, "skip": False,
            "expected": failure.get('message'),
        }]

        # Success is true
        expected = True, success.get('message')
        returned = jupiter_obj._check_skip_notification_(success)
        self.assertEqual(expected, returned)

        # Cases where alarm is triggered
        for test in skip_tests:
            mock_boolean.return_value = test.get("use_cal")
            mock_last_fail.return_value = test.get("last_failed")
            mock_time.return_value = test.get("skip")
            expected = False, test.get("expected")
            returned = jupiter_obj._check_skip_notification_(failure)
            self.assertEqual(expected, returned)

        # Skip the notify
        mock_boolean.return_value = True
        mock_last_fail.return_value = True
        mock_time.return_value = True
        mock_datetime.now.return_value = self.example_today
        skip_boolean, skip_message = jupiter_obj._check_skip_notification_(self.example_summarized_results)
        # Cannot mock datetime and return result contains exact time to the second
        self.assertIn("Notification is skipped at", skip_message)

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

    @patch('watchmen.process.jupiter.mv_key')
    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_state(self, mock_dumps, mock_content, mock_mv_key):
        jupiter_obj = Jupiter(event=None, context=None)
        mock_dumps.return_value = self.example_summarized_results
        results = mock_dumps.return_value
        mock_content.return_value = True
        self.assertTrue(mock_content.return_value)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = jupiter_obj.log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = jupiter_obj.log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter._check_last_failure')
    @patch('watchmen.process.jupiter.raise_alarm')
    def test_summarize(self, mock_alarm, mock_fail):
        jupiter_obj = Jupiter(event=None, context=None)
        # Failure setup
        failures = self.example_failed.get('failure')

        failed_message = []
        for item in failures:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            failed_message.append(msg)
        failed_message = '{}\n\n\n{}'.format('\n\n'.join(failed_message), self.check_logs)

        first_failure = 's' if len(failures) > 1 else ' - {}'.format(failures[0].get('name'))
        failed_subject = '{}{}'.format(self.error_subject, first_failure)

        #  Empty results setup
        empty_message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(self.example_empty, sort_keys=True, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_endpoints, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_validated, indent=2)
        )
        empty_message = "{}\n\n\n{}".format(empty_message, self.no_results)

        test_results = [{
            "results": self.example_no_failures, "last_failed": False, "expected": {
                "message": self.success_message, "subject": self.success_subject, "success": True,
            }
        }, {
            "results": self.example_failed, "last_failed": True, "expected": {
                "last_failed": True, "message": failed_message, "subject": failed_subject, "success": False,
            }
        }, {
            "results": self.example_empty, "last_failed": False, "expected": {
                 "last_failed": False, "message": empty_message, "subject": self.error_jupiter, "success": False,
            }
        }]

        for test in test_results:
            mock_fail.return_value = test.get('last_failed')
            results = test.get('results')
            expected = test.get('expected')
            returned = jupiter_obj.summarize(results, self.example_endpoints, self.example_validated)
            self.assertEqual(expected, returned)

        # Results DNE
        results = None
        expected = {
            "last_failed": True, "message": self.results_dne, "subject": self.error_jupiter, "success": False,
            }
        mock_fail.return_value = True
        returned = jupiter_obj.summarize(results, None, None)
        self.assertEqual(expected, returned)
