import unittest, json
from mock import patch, mock_open
from watchmen.jupiter import main, notify, load_endpoints, CHECK_LOGS, NO_RESULTS_MESSAGE


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.example_exception_message = "Something failed"
        self.example_success_result = {'failure': [], 'success': [{'name': 'passed'}]}
        self.example_failure_result = {'failure': [{'name': 'failed', '_err': 'did not work'}], 'success': []}
        self.example_empty_result = {'failure': [], 'success': []}
        self.example_filename = "points.json"

    @patch('watchmen.jupiter.raise_alarm')
    def test_notify(self, mock_alarm):
        # No failures
        expected_result = None
        returned_result = notify(self.example_success_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # Failures exist
        message = ""
        for fail in self.example_failure_result['failure']:
            message += "'{}' failed because of error '{}'. Check for empty file or dict.".format(fail['name'], fail['_err']) + '\n'
        expected_result = message + CHECK_LOGS
        returned_result = notify(self.example_failure_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

        # Empty Error
        expected_result = "{} {}".format(NO_RESULTS_MESSAGE, self.example_filename)
        returned_result = notify(self.example_empty_result, self.example_filename)
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.jupiter.raise_alarm')
    @patch('json.load')
    def test_load_endpoints(self, mock_json_load, mock_alarm):
        good_data = """
        [{
            "name": "happy data",
            "more": [{
                "name": "nested data"
            }]
        }]
        """
        # File not empty and can be opened
        with patch('builtins.open', mock_open(read_data=good_data)) as mock_file:
            print "I still do not understand how to mock json.load properly"


    @patch('watchmen.jupiter.load_endpoints')
    def test_main(self, mock_load_ep):
        




    # @patch('watchmen.jupiter.raise_alarm')
    # @patch('json.loads')
    # def test_main(self, mock_load, mock_alarm):
    #     data = ""
    #     with patch('builtins.open', mock_open(read_data=data)) as mock_file:
    #         mock_load = mock_file.return_value
            # mock_load.assert_called_with(mock_file)

        # m.side_effect = Exception(self.example_exception_message)
        # # Failure to open file
        # expected_result = "ERROR: '{}'{}'{}'".format(ENDPOINT_FILE, OPEN_FILE_ERROR, ENDPOINT_FILE)
        # returned_result = main(None, None)
        # self.assertEqual(expected_result, returned_result)








