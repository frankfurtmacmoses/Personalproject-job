import unittest
from datetime import datetime, timedelta
from mock import patch
import pytz

from watchmen.models.ozymandias import Ozymandias


class TestOzymandias(unittest.TestCase):

    def setUp(self):
        self.example_filename = \
            (datetime.now(pytz.utc) - timedelta(days=2)).strftime("%Y%m%d").replace('/', '') + '.compressed'
        self.example_exception_message = "Something is not working"
        self.example_message_chart = {
            None: "Ozymandias failed due to "
                  "the following:\n\n{}\n\nPlease check the logs!",
            False: "ERROR: " + self.example_filename + " could not "
                   "be found in hancock/neustar! Please check S3 and neustar VM!",
            True: "Neustar data found on S3! File found: " + self.example_filename,
        }
        self.example_result_dict = {
            "details": {},
            "disable_notifier": False,
            "message": self.example_message_chart.get(False),
            "observed_time": "2018-12-18T00:00:00+00:00",
            "result_id": 0,
            "success": False,
            "source": "Ozymandias",
            "state": "FAILURE",
            "subject": "Ozymandias neustar data monitor detected a failure!",
            "target": "Neustar",
        }

    def test_create_message(self):
        """
        test watchmen.models.ozymandias :: Ozymandias :: _create_message
        """
        found_file_chart = [True, False, None]
        ozymandias_obj = Ozymandias()
        for found_file in found_file_chart:
            expected = self.example_message_chart.get(found_file)
            result = ozymandias_obj._create_message(found_file, {})
            self.assertEqual(expected, result)
            pass

    def test_create_result(self):
        """
        test watchmen.models.ozymandias:: Ozymandias :: _create_result
        """
        expected = self.example_result_dict
        ozymandias_obj = Ozymandias()
        result = ozymandias_obj._create_result(
            False,
            "FAILURE",
            "Ozymandias neustar data monitor detected a failure!",
            self.example_message_chart.get(False)).to_dict()
        # since ozymandias does not give observed time, we don't test the time here
        result['observed_time'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, result)

    @patch('watchmen.models.ozymandias.validate_file_on_s3')
    def test_check_file_exist(self, mock_validate_file):
        """
        test watchmen.models.ozymandias:: Ozymandias :: _check_file_exist
        """
        ozymandias_obj = Ozymandias()
        tests = [{
            "is_valid": True,
            "result": True,
            "tb": None,
        }, {
            "is_valid": False,
            "result": False,
            "tb": None,
        }]
        for test in tests:
            expected = test.get("result")
            expected_tb = test.get("tb")
            mock_validate_file.return_value = test.get("is_valid")
            result, tb = ozymandias_obj._check_file_exists()
            self.assertEqual(expected, result)
            self.assertEqual(expected_tb, tb)

        # Exception occurred
        mock_validate_file.side_effect = Exception(self.example_exception_message)
        result, result_tb = ozymandias_obj._check_file_exists()
        self.assertEqual(result, None)
        self.assertTrue(self.example_exception_message in result_tb)

    @patch('watchmen.models.ozymandias.Ozymandias._check_file_exists')
    @patch('watchmen.models.ozymandias.Ozymandias._create_message')
    def test_monitor(self, mock_create_message, mock_check_file_exists):
        """
        test watchmen.models.ozymandias:: Ozymandias :: monitor
        """
        ozymandias_obj = Ozymandias()
        mock_create_message.return_value = self.example_message_chart.get(False)
        mock_check_file_exists.return_value = False, "string"
        expected = self.example_result_dict
        result = ozymandias_obj.monitor().to_dict()

        # since ozymandias does not give observed time, we don't test the time here
        result['observed_time'] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(result, expected)
