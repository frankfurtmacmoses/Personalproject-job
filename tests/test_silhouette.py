import unittest
from mock import patch
from watchmen.silhouette import main, process_status, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestSilhouette(unittest.TestCase):

    def setUp(self):
        self.example_success_json = {"STATE": "COMPLETED"}
        self.example_failed_json = {"STATE": "ERROR"}

    @patch('json.loads')
    @patch('watchmen.silhouette.Watchmen')
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

    @patch('watchmen.silhouette.process_status')
    def test_main(self, mock_process_status):
        mock_process_status.return_value = True
        expected_result = SUCCESS_MESSAGE
        returned_result = main()
        self.assertEqual(expected_result, returned_result)
        mock_process_status.return_value = False
        expected_result = FAILURE_MESSAGE
        returned_result = main()
        self.assertEqual(expected_result, returned_result)



