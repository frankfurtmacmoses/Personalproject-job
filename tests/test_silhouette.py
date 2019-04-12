import unittest
from mock import patch
from watchmen.process.silhouette import main, process_status, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestSilhouette(unittest.TestCase):

    def setUp(self):
        self.example_success_json = {"STATE": "COMPLETED"}
        self.example_failed_json = {"STATE": "UNCOMPLETED"}
        self.example_exception_msg = "Something went wrong"
        self.example_event = {}
        self.example_context = {}

    @patch('json.loads')
    @patch('watchmen.process.silhouette.Watchmen')
    def test_process_status(self, mock_watchmen, mock_json_loads):
        # Test when process produced completed result
        mock_json_loads.return_value = self.example_success_json
        expected_result = True
        returned_result = process_status()
        self.assertEqual(expected_result, returned_result)
        # Test when process produced non-completed result
        mock_json_loads.return_value = self.example_failed_json
        expected_result = False
        returned_result = process_status()
        self.assertEqual(expected_result, returned_result)
        # Test when status.json doesn't exist
        mock_watchmen.get_file_contents_s3.return_value = None
        expected_result = False
        returned_result = process_status()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.silhouette.raise_alarm')
    @patch('watchmen.process.silhouette.process_status')
    def test_main(self, mock_process_status, mock_raise_alarm):
        # Test when lookalike is up
        mock_process_status.return_value = True
        expected_result = SUCCESS_MESSAGE
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        # Test when lookalike is down
        mock_process_status.return_value = False
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
        self.assertEqual(expected_result, returned_result)
        # Test when exception is thrown
        mock_process_status.side_effect = Exception(self.example_exception_msg)
        expected_result = FAILURE_MESSAGE
        returned_result = main(self.example_event, self.example_context)
        self.assertEqual(expected_result, returned_result)
