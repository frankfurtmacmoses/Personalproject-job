import unittest
from moto import mock_sns
from mock import patch
from watchmen.process.ozymandias import main, SUCCESS_MESSAGE, FAILURE_MESSAGE


class TestOzymandias(unittest.TestCase):

    @mock_sns
    @patch('watchmen.process.ozymandias.Watchmen.validate_file_on_s3')
    @patch('watchmen.process.ozymandias.raise_alarm')
    def test_main(self, mock_alarm, mock_validate_on_s3):
        mock_validate_on_s3.return_value = True
        expected_result = SUCCESS_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        mock_validate_on_s3.return_value = False
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
        mock_validate_on_s3.side_effect = Exception('Error!')
        expected_result = FAILURE_MESSAGE
        returned_result = main(None, None)
        self.assertEqual(expected_result, returned_result)
