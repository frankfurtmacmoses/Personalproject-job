import unittest
import json
from mock import patch

from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.jupiter import notify, load_endpoints, check_endpoints, main, RESULTS_DNE, SUCCESS_MESSAGE, \
    CHECK_LOGS, NO_RESULTS


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.example_bad_list = [{"name": "NoPath"}, {}]
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
        self.example_empty = {"failure": [], "success": []}
        self.example_endpoints = [{"name": "endpoint", "path": "example"}, {"name": "Used for testing"}]
        self.example_exception_message = "Something failed"
        self.example_failed = {"failure": [{"name": "Failure", "path": "filler/fail", "_err": "something"},
                                           {"key": "Big fail"}], "success": []}
        self.example_few_validated = []
        self.example_invalid_paths = [{"key": "that fails"}]
        self.example_local_endpoints = [{"name": "local", "path": "s3/failed"}]
        self.example_validated_list = [{"name": "HaveName", "path": "have/path"}, {"path": "pathWith/NoName"}]
        self.example_no_failures = {"failure": [], "success": [{"name": "succeeded"}]}
        self.example_notification = "Endpoints have been checked"
        self.example_passed_endpoints = [{"name": "good endpoint", "path": "good/path"}]
        self.example_results_mix = {'failure': [{'name': 'failed'}], 'success': [{'name': 'passed'}]}
        self.example_results_passed = {'failure': [{'name': 'failed'}], 'success': [{'name': 'passed'}]}
        self.example_valid_paths = [{"name": "I will work", "path": "here/is/path"}]
        self.example_validated = [{"name": "endpoint", "path": "example"}]
        self.example_variety_endpoints = [{"name": "endpoint", "path": "cool/path"}, {"key": "bad endpoint"}]

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

    @patch('watchmen.process.jupiter.notify')
    @patch('watchmen.process.jupiter.ServiceChecker.get_validated_paths')
    @patch('watchmen.process.jupiter.ServiceChecker.start')
    @patch('watchmen.process.jupiter.check_endpoints')
    @patch('watchmen.process.jupiter.load_endpoints')
    def test_main(self, mock_load_endpoints, mock_check_endpoints, mock_start, mock_validate, mock_notify):
        # set endpoints
        mock_load_endpoints.return_value = self.example_variety_endpoints
        mock_check_endpoints.return_value = self.example_passed_endpoints

        test_checker = ServiceChecker(mock_check_endpoints.return_value)

        # Make sure endpoints go through check and return results
        test_checker.start.return_value = self.example_results_mix
        results = test_checker.start()
        self.assertIsNotNone(results)
        test_checker.start.assert_called_with()

        test_checker.get_validated_paths.return_value = self.example_results_passed
        passed_results = test_checker.get_validated_paths()
        self.assertIsNotNone(passed_results)
        test_checker.get_validated_paths.assert_called_with()

        # Notify upon results
        mock_notify.return_value = self.example_notification
        expected_result = mock_notify.return_value
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_notify(self, mock_alarm):
        # No results
        expected_result = RESULTS_DNE
        returned_result = notify(None, None, None)
        self.assertEqual(expected_result, returned_result)

        # No failures
        expected_result = SUCCESS_MESSAGE
        returned_result = notify(self.example_no_failures, self.example_endpoints, self.example_validated)
        self.assertEqual(expected_result, returned_result)

        # Failures exist
        failed = self.example_failed.get('failure')
        self.assertIsInstance(failed, list)
        messages = []
        for item in failed:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            messages.append(msg)
        message = '{}\n\n\n{}'.format('\n\n'.join(messages), CHECK_LOGS)
        expected_result = message
        returned_result = notify(self.example_failed, self.example_endpoints, self.example_validated)
        self.assertEqual(expected_result, returned_result)

        # Empty error
        split_line = '-' * 80
        message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(self.example_empty, sort_keys=True, indent=2),
            split_line,
            json.dumps(self.example_endpoints, indent=2),
            split_line,
            json.dumps(self.example_validated, indent=2)
        )
        message = "{}\n\n\n{}".format(message, NO_RESULTS)
        expected_result = message
        returned_result = notify(self.example_empty, self.example_endpoints, self.example_validated)
        self.assertEqual(expected_result, returned_result)
