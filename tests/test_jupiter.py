import unittest
import json
from mock import patch

from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.jupiter import CHECK_LOGS, CHECK_TIME_UTC, ERROR_JUPITER, ERROR_SUBJECT, NO_RESULTS, RESULTS_DNE,\
    SUCCESS_MESSAGE
from watchmen.process.jupiter import check_endpoints, load_endpoints, log_result, log_state, main, notify, summarize


class TestJupiter(unittest.TestCase):

    def setUp(self):
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
        self.example_prefix = "watchmen/jupiter/{}/{}".format("2019", CHECK_TIME_UTC.strftime(self.example_date_format))
        self.example_results_mix = {
            'failure': [{
                'name': 'failed'
            }],
            'success': [{
                'name': 'passed'
            }]}
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

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_check_endpoints(self, mock_alarm):
        test_bad_messages = ['There is not a path to check for: HaveName', 'There is not a path to check for: '
                                                                           'There is not a name available']
        # check that can't find paths in bad list
        for item in self.example_bad_list:
            self.assertEqual(False, "path" in item)

        # check that can find paths in validated list
        for item in self.example_validated_list:
            self.assertEqual(True, "path" in item)

        # Check that bad messages match
        message = '\n'.join(test_bad_messages)
        self.assertEqual(self.example_bad_messages, message)

        # Check validated is greater than min
        self.assertTrue(len(self.example_validated_list) > 0)
        # If validated has too few to be checked
        self.assertFalse(len(self.example_few_validated) > 0)
        expected_result = None
        returned_result = check_endpoints(self.example_few_validated)
        self.assertEqual(expected_result, returned_result)

        expected_result = self.example_validated_list
        returned_result = check_endpoints(self.example_bad_list+self.example_validated_list)
        self.assertEqual(expected_result, returned_result)

    @patch("watchmen.process.jupiter.raise_alarm")
    @patch("watchmen.process.jupiter.ENDPOINTS_DATA")
    @patch("watchmen.process.jupiter.check_endpoints")
    @patch("watchmen.process.jupiter.json.loads")
    @patch("watchmen.process.jupiter.get_content")
    @patch("watchmen.process.jupiter.settings")
    def test_load_endpoints(self, mock_settings, mock_get_content, mock_loads, mock_check, mock_endpoints, mock_alarm):
        # set default endpoints and content
        mock_endpoints.return_value = self.example_local_endpoints
        mock_get_content.return_value = self.example_data

        # load succeeds and there are validated endpoints
        mock_loads.return_value = self.example_valid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        mock_check.return_value = self.example_valid_paths
        self.assertIsInstance(mock_check.return_value, list)
        expected_result = mock_check.return_value
        returned_result = load_endpoints()
        self.assertEqual(expected_result, returned_result)

        # load succeeds and there are no validated endpoints
        mock_loads.return_value = self.example_invalid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        mock_check.return_value = []
        expected_result = self.example_local_endpoints
        returned_result = (load_endpoints()).return_value
        self.assertEqual(expected_result, returned_result)

        # load fails
        mock_loads.side_effect = Exception(self.example_exception_message)
        expected_result = mock_endpoints.return_value
        returned_result = (load_endpoints()).return_value
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_result(self, mock_dumps, mock_content):
        mock_dumps.return_value = self.example_results_mix
        results = mock_dumps.return_value
        expected = self.example_prefix
        returned = log_result(results)
        self.assertIn(expected, returned)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = log_result(results)
        self.assertIn(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = log_result(results)
        self.assertIn(expected, returned)

    @patch('watchmen.process.jupiter.mv_key')
    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_state(self, mock_dumps, mock_content, mock_mv_key):
        mock_dumps.return_value = self.example_summarized_results
        results = mock_dumps.return_value
        mock_content.return_value = True
        self.assertTrue(mock_content.return_value)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.notify')
    @patch('watchmen.process.jupiter.log_state')
    @patch('watchmen.process.jupiter.summarize')
    @patch('watchmen.process.jupiter.ServiceChecker.get_validated_paths')
    @patch('watchmen.process.jupiter.log_result')
    @patch('watchmen.process.jupiter.ServiceChecker.start')
    @patch('watchmen.process.jupiter.check_endpoints')
    @patch('watchmen.process.jupiter.load_endpoints')
    def test_main(self, mock_load_endpoints, mock_check_endpoints, mock_start, mock_log_result, mock_validate,
                  mock_summarize, mock_logs, mock_notify):
        # set endpoints
        mock_load_endpoints.return_value = self.example_variety_endpoints
        mock_check_endpoints.return_value = self.example_passed_endpoints

        test_checker = ServiceChecker(mock_check_endpoints.return_value)

        # Make sure endpoints go through check and return results
        test_checker.start.return_value = self.example_results_mix
        results = test_checker.start()
        self.assertIsNotNone(results)
        test_checker.start.assert_called_with()

        # Log results
        mock_log_result.return_value = self.example_prefix
        prefix = mock_log_result()
        self.assertIsNotNone(prefix)
        mock_log_result.assert_called_with()

        # Get validated results
        test_checker.get_validated_paths.return_value = self.example_results_passed
        passed_results = test_checker.get_validated_paths()
        self.assertIsNotNone(passed_results)
        test_checker.get_validated_paths.assert_called_with()

        # Summarize results
        mock_summarize.return_value = self.example_summarized_results
        summarized_results = mock_summarize()
        self.assertIsNotNone(summarized_results)
        mock_summarize.assert_called_with()

        #  Log state
        mock_logs()
        mock_logs.assert_called_with()

        # Notify results
        mock_notify.return_value = self.example_status
        status = mock_notify()
        self.assertIsNotNone(status)
        mock_notify.assert_called_with()

        # Verify return of  sanitized results
        expected_result = status
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.jupiter.get_boolean')
    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter._check_last_failure')
    @patch('watchmen.process.jupiter._check_skip_notification')
    def test_notify(self, mock_skip, mock_last_fail, mock_alarm, mock_boolean):
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
            "expected": "FAILURES occurred! Check the logs for more details!",
        }, {
            "use_cal": True, "last_failed": False, "skip": False,
            "expected": "FAILURES occurred! Check the logs for more details!",
        }, {
            "use_cal": True, "last_failed": True, "skip": False,
            "expected": "FAILURES occurred! Check the logs for more details!",
        }]

        # Success is true
        expected = SUCCESS_MESSAGE
        returned = notify(success)
        self.assertEqual(expected, returned)

        # Cases where alarm is triggered
        for test in skip_tests:
            mock_boolean.return_value = test.get("use_cal")
            mock_last_fail.return_value = test.get("last_failed")
            mock_skip.return_value = test.get("skip")
            expected = test.get("expected")
            returned = notify(failure)
            self.assertEqual(expected, returned)

        # Skip the notify
        mock_boolean.return_value = True
        mock_last_fail.return_value = True
        mock_skip.return_value = True
        # Cannot mock datetime and return result contains exact time to the second
        self.assertIn("Notification is skipped at", notify(self.example_summarized_results))

    @patch('watchmen.process.jupiter._check_last_failure')
    @patch('watchmen.process.jupiter.raise_alarm')
    def test_summarize(self, mock_alarm, mock_fail):
        # Failure setup
        failures = self.example_failed.get('failure')

        failed_message = []
        for item in failures:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            failed_message.append(msg)
        failed_message = '{}\n\n\n{}'.format('\n\n'.join(failed_message), CHECK_LOGS)

        first_failure = 's' if len(failures) > 1 else ' - {}'.format(failures[0].get('name'))
        failed_subject = '{}{}'.format(ERROR_SUBJECT, first_failure)

        #  Empty results setup
        split_line = '-' * 80
        empty_message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(self.example_empty, sort_keys=True, indent=2),
            split_line,
            json.dumps(self.example_endpoints, indent=2),
            split_line,
            json.dumps(self.example_validated, indent=2)
        )
        empty_message = "{}\n\n\n{}".format(empty_message, NO_RESULTS)

        test_results = [{
            "results": self.example_no_failures, "last_failed": False, "expected": {
                "message": SUCCESS_MESSAGE, "success": True,
            }
        }, {
            "results": self.example_failed, "last_failed": True, "expected": {
                "last_failed": True, "message": failed_message, "subject": failed_subject, "success": False,
            }
        }, {
            "results": self.example_empty, "last_failed": False, "expected": {
                 "last_failed": False, "message": empty_message, "subject": ERROR_JUPITER, "success": False,
            }
        }]

        for test in test_results:
            mock_fail.return_value = test.get('last_failed')
            results = test.get('results')
            expected = test.get('expected')
            returned = summarize(results, self.example_endpoints, self.example_validated)
            self.assertEqual(expected, returned)

        # Results DNE
        results = None
        expected = {
            "last_failed": True, "message": RESULTS_DNE, "subject": ERROR_JUPITER, "success": False,
            }
        mock_fail.return_value = True
        returned = summarize(results, None, None)
        self.assertEqual(expected, returned)
