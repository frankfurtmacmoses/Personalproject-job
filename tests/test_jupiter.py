import unittest
from mock import patch
from watchmen.jupiter import main, notify, load_endpoints, CHECK_LOGS, NO_RESULTS_MESSAGE, OPEN_FILE_ERROR, \
    SUCCESS_MESSAGE


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
        self.example_good_data = """
                [{
                    "name": "happy data",
                    "more": [{
                        "name": "nested data"
                    }]
                }]
                """

    @patch('watchmen.jupiter.raise_alarm')
    def test_notify(self, mock_alarm):
        # No failures
        expected_result = None
        returned_result = notify(self.example_success_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # Failures exist
        message = ""
        for fail in self.example_failure_result['failure']:
            message += "'{}' failed because of error '{}'. Check for empty file or dict.".format(fail['name'],
                                                                                                 fail['_err']) + '\n'
        expected_result = message + CHECK_LOGS
        returned_result = notify(self.example_failure_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # Empty Error
        expected_result = "{} {}".format(NO_RESULTS_MESSAGE, self.example_filename)
        returned_result = notify(self.example_empty_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

    @patch("watchmen.jupiter.raise_alarm")
    @patch("json.load")
    @patch("__builtin__.open")
    def test_load_endpoints(self, m_open, mock_json_load, mock_alarm):
        # File not empty and can be opened
        mock_json_load.return_value = self.example_good_data
        expected_result = self.example_good_data
        returned_result = load_endpoints(self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # File empty and/or cannot be opened
        m_open.side_effect = Exception(self.example_exception_message)
        expected_result = "ERROR: '{}'{}'{}'".format(self.example_filename, OPEN_FILE_ERROR, self.example_filename)
        returned_result = load_endpoints(self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # File cannot load
        mock_json_load.side_effect = Exception(self.example_exception_message)
        expected_result = "ERROR: '{}'{}'{}'".format(self.example_filename, OPEN_FILE_ERROR, self.example_filename)
        returned_result = load_endpoints(self.example_filename)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.jupiter.notify')
    @patch('watchmen.jupiter.ServiceChecker.start')
    @patch('watchmen.jupiter.load_endpoints')
    def test_main(self, mock_load_eps, mock_checker, mock_notify):

        # Exception or error occured while loading endpoints file
        mock_load_eps.return_value = self.example_exception_message
        expected_result = self.example_exception_message
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)

        # Endpoints are returned
        mock_load_eps.return_value = self.example_list

        # There is a notification message
        mock_notify.return_value = self.example_bad_notify
        expected_result = self.example_bad_notify
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)

        # Everything worked
        mock_notify.return_value = ""
        expected_result = SUCCESS_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
