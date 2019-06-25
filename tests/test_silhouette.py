import unittest
from mock import patch
from watchmen.process.silhouette import SUCCESS_MESSAGE, FAILURE_MESSAGE, EXCEPTION_MESSAGE
from watchmen.process.silhouette import main, process_status, check_process_status, notify


class TestSilhouette(unittest.TestCase):

    def setUp(self):
        self.example_success_json = {"STATE": "COMPLETED"}
        self.example_failed_json = {"STATE": "UNCOMPLETED"}
        self.example_exception_msg = "Something went wrong"
        self.example_event = {}
        self.example_context = {}
        self.example_status = "The file was checked"
        self.example_traceback = "Fake ERROR on line 67\n   Something could not open\n   So it broke"

    @patch('watchmen.process.silhouette.raise_alarm')
    @patch('watchmen.process.silhouette.process_status')
    def test_check_process_status(self, mock_process, mock_alarm):
        # Process check found file
        mock_process.return_value = True
        expected = True
        returned = check_process_status()
        self.assertEqual(expected, returned)

        # check did not find file
        mock_process.return_value = False
        expected = False
        returned = check_process_status()
        self.assertEqual(expected, returned)

        # Check raised an exception
        mock_process.side_effect = Exception(self.example_exception_msg)
        expected = None
        returned = check_process_status()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.silhouette.notify')
    @patch('watchmen.process.silhouette.check_process_status')
    def test_main(self, mock_check, mock_notify):
        # Find the check status
        mock_check.return_value = False
        check_result = mock_check()
        self.assertIsNotNone(check_result)
        mock_check.assert_called_with()

        # Notify
        mock_notify.return_value = self.example_status
        status = mock_notify()
        self.assertIsNotNone(status)
        mock_notify.assert_called_with()

        # check return
        expected = self.example_status
        returned = main(None, None)
        self.assertEqual(expected, returned)

    @patch('json.loads')
    @patch('watchmen.process.silhouette.get_file_contents_s3')
    def test_process_status(self, mock_get_contents, mock_json_loads):
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
        mock_get_contents.return_value = None
        expected_result = False
        returned_result = process_status()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.silhouette.raise_alarm')
    def test_notify(self, mock_alarm):
        test_results = [
            {"file_exists": True, "expected": SUCCESS_MESSAGE},
            {"file_exists": False, "expected": FAILURE_MESSAGE},
            {"file_exists": None, "expected": EXCEPTION_MESSAGE}
        ]

        for result in test_results:
            file_exists = result.get("file_exists")
            expected = result.get("expected")
            returned = notify(file_exists)
            self.assertEqual(expected, returned)
