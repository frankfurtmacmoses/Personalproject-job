import unittest
from mock import patch

from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.jupiter import notify, load_endpoints, check_endpoints, main, RESULTS_DNE


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.example_exception_message = "Something failed"
        self.example_success_result = {'failure': [], 'success': [{'name': 'passed'}]}
        self.example_failure_result = {'failure': [{'name': 'failed', '_err': 'did not work'},
                                                   {'name': 'big failure', '_err': 'broken!'}], 'success': []}
        self.example_empty_result = {'failure': [], 'success': []}
        self.example_filename = "points.json"
        self.example_list = ["i", "am", 4, ['list']]
        self.example_bad_notify = "something went wrong"
        self.example_bad_messages = "There is not a path to check for: HaveName\n" \
                                    "There is not a path to check for: There is not a name available"
        self.example_endpoints = [{"name": "back up", "path": "s3/did/not/work"}]

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_check_endpoints(self, mock_alarm):
        test_bad_list = [{"name": "NoPath"}, {}]
        test_validated_list = [{"name": "HaveName", "path": "have/path"}, {"path": "pathWith/NoName"}]
        test_bad_messages = ['There is not a path to check for: HaveName', 'There is not a path to check for: '
                                                                           'There is not a name available']

        # check that can't find paths in bad list
        for item in test_bad_list:
            self.assertEqual(False, "path" in item)

        # check that can find paths in validated list
        for item in test_validated_list:
            self.assertEqual(True, "path" in item)

        # Check that bad messages match
        message = '\n'.join(test_bad_messages)
        self.assertEqual(self.example_bad_messages, message)

        expected_result = test_validated_list
        returned_result = check_endpoints(test_bad_list+test_validated_list)
        self.assertEqual(expected_result, returned_result)

    @patch("watchmen.process.jupiter.raise_alarm")
    @patch("watchmen.process.jupiter.endpoints_data")
    @patch("watchmen.process.jupiter.check_endpoints")
    @patch("watchmen.process.jupiter.json.loads")
    @patch("watchmen.process.jupiter.get_content")
    @patch("watchmen.process.jupiter.settings")
    def test_load_endpoints(self, mock_settings, mock_get_content, mock_loads, mock_check, mock_endpoints, mock_alarm):
        test_data = """[{
                            "name": "happy data from s3",
                            "path": "success",
                            "more": [{
                                "name": "nested data"
                            }]
                        },{
                            "name": "missing data"
                        }]
                        """
        test_valid_paths = [{"name": "I will work", "path": "here/is/path"}]
        test_invalid_paths = [{"key": "that fails"}]
        test_local_endpoints = [{"name": "local", "path": "s3/failed"}]

        # set default endpoints and content
        mock_endpoints.return_value = test_local_endpoints
        mock_get_content.return_value = test_data

        # load succeeds and there are validated endpoints
        mock_loads.return_value = test_valid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        mock_check.return_value = test_valid_paths
        self.assertIsInstance(mock_check.return_value, list)
        expected_result = mock_check.return_value
        returned_result = load_endpoints()
        self.assertEqual(expected_result, returned_result)

        # load succeeds and there are no validated endpoints
        mock_loads.return_value = test_invalid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        mock_check.return_value = []
        expected_result = test_local_endpoints
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
        test_variety_endpoints = [{"name": "endpoint", "path": "cool/path"}, {"key": "bad endpoint"}]
        test_passed_endpoints = [{"name": "good endpoint", "path": "good/path"}]
        test_results_mix = {'failure': [{'name': 'failed'}], 'success': [{'name': 'passed'}]}
        test_results_passed = {'failure': [{'name': 'failed'}], 'success': [{'name': 'passed'}]}
        test_notification = "Endpoints have been checked"

        mock_load_endpoints.return_value = test_variety_endpoints
        mock_check_endpoints.return_value = test_passed_endpoints

        test_checker = ServiceChecker(mock_check_endpoints.return_value)

        test_checker.start.return_value = test_results_mix
        results = test_checker.start()
        self.assertIsNotNone(results)
        test_checker.start.assert_called_with()

        test_checker.get_validated_paths.return_value = test_results_passed
        passed_results = test_checker.get_validated_paths()
        self.assertIsNotNone(passed_results)
        test_checker.get_validated_paths.assert_called_with()

        mock_notify.return_value = test_notification
        expected_result = mock_notify.return_value
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_notify(self, mock_dumps, mock_alarm):
        test_failed = [{'name': 'failed', '_err': 'did not work'}, {'name': 'big failure', '_err': 'broken!'}]
        test_passed = [{'name': 'passed'}]
        #test_empty = {'failure': [], 'success': []}

        # No results
        expected_result = RESULTS_DNE
        returned_results = notify(None, None, None)
        self.assertEqual(expected_result, returned_results)

        # No failures

        # Failures exist

        # Empty error




