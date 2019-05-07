import unittest
from moto import mock_sns
from mock import patch
from watchmen.process.ozymandias import SUCCESS_MESSAGE, FAILURE_MESSAGE, EXCEPTION_MESSAGE
from watchmen.process.ozymandias import main, check_file_exists, notify


class TestOzymandias(unittest.TestCase):
    def setUp(self):
        self.example_status = "The file was checked"
        self.example_file_status = False
        self.example_traceback = "This is a traceback"

    @patch('watchmen.process.ozymandias.traceback.format_exc')
    @patch('watchmen.process.ozymandias.Watchmen.validate_file_on_s3')
    def test_check_file_exists(self, mock_validate, mock_trace):
        # File exists
        mock_validate.return_value = True
        expected = True
        returned = check_file_exists()
        self.assertEqual(expected, returned)

        # File does not exist
        mock_validate.return_value = False
        expected = False
        returned = check_file_exists()
        self.assertEqual(expected, returned)

        # Exception occurred
        mock_validate.side_effect = Exception('Error!')
        mock_trace.return_value = self.example_traceback
        expected = self.example_traceback
        returned = check_file_exists()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.ozymandias.notify')
    @patch('watchmen.process.ozymandias.check_file_exists')
    def test_main(self, mock_check, mock_notify):
        mock_check.return_value = self.example_file_status
        mock_notify.return_value = self.example_status

        # Get the result from checking the file
        result = mock_check()
        self.assertIsNotNone(result)
        mock_check.assert_called_with()
        # Send them through notify
        status = mock_notify()
        self.assertIsNotNone(status)
        mock_notify.assert_called_with()

        # If nothing caused an exception
        expected = self.example_status
        returned = main(None, None)
        self.assertEqual(expected, returned)

    @mock_sns
    @patch('watchmen.process.ozymandias.raise_alarm')
    def test_notify(self, mock_alarm):
        test_results = [
            {"file_exists": True, "expected": SUCCESS_MESSAGE},
            {"file_exists": False, "expected": FAILURE_MESSAGE},
            {"file_exists": self.example_traceback, "expected": EXCEPTION_MESSAGE}
        ]

        for test in test_results:
            file_status = test.get("file_exists")
            expected = test.get("expected")
            returned = notify(file_status)
            self.assertEqual(expected, returned)
