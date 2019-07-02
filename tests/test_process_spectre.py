import unittest
from datetime import datetime
import pytz

from mock import patch
from watchmen.models.spectre import Spectre


class TestSpectre(unittest.TestCase):

    def setUp(self):
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_filename = "2018/12/gt_mpdns_20181217.zip"
        self.example_exception_message = "Something is not working"
        self.example_status = "The file was checked"
        self.example_message_chart = {
            None: 'Spectre for Georgia Tech failed '
                  'on \n\t"2018/12/gt_mpdns_20181217.zip" \ndue to '
                  'the Exception:\n\n{}\n\nPlease check the logs!',
            False: "ERROR: 2018/12/gt_mpdns_20181217.zip"
                   "could not be found in cyber-intel/hancock/georgia_tech/! "
                   "Please check S3 and Georgia Tech logs!",
            True: "Georgia Tech Feed data found on S3!",
        }
        self.example_result_dict = {
            "details": {},
            "disable_notifier": False,
            "message": self.example_message_chart.get(False),
            "observed_time": "2018-12-18T00:00:00+00:00",
            "result_id": 0,
            "success": False,
            "source": "Spectre",
            "state": "FAILURE",
            "subject": "Spectre Georgia Tech data monitor detected a failure!",
            "target": "Georgia Tech S3",
        }

    @patch('watchmen.models.spectre.validate_file_on_s3')
    def test_check_if_found_file(self, mock_validate):
        """
        test watchmen.models.spectre:: Spectre :: _check_if_found_file
        """
        spectre_obj = Spectre()
        tests = [
            {
                "validate_return_value": True,
                "expected": True,
            }, {
                "validate_return_value": False,
                "expected": False,
            }
        ]
        for test in tests:
            mock_validate.return_value = test.get("validate_return_value")
            expected = test.get("expected")
            result, tb = spectre_obj._check_if_found_file(self.example_filename)
            self.assertEqual(result, expected)

        # Exception occurred
        mock_validate.side_effect = Exception(self.example_exception_message)
        result, result_tb = spectre_obj._check_if_found_file(self.example_filename)
        self.assertEqual(result, None)
        self.assertTrue(self.example_exception_message in result_tb)

    def test_create_message(self):
        """
        test watchmen.models.spectre:: Spectre :: _create_message
        """
        file_founds = [True, False, None]
        spectre_obj = Spectre()
        for file_found in file_founds:
            expected = self.example_message_chart.get(file_found)
            result = spectre_obj._create_message(self.example_filename, file_found, {})
            self.assertEqual(result, expected)

    def test_create_result(self):
        """
        test watchmen.models.spectre:: Spectre :: _create_result
        """
        expected = self.example_result_dict
        spectre_obj = Spectre()
        result = spectre_obj._create_result(
            False,
            "FAILURE",
            "Spectre Georgia Tech data monitor detected a failure!",
            self.example_message_chart.get(False)).to_dict()
        # since spectre does not give observed time, we don't test the time here
        result['observed_time'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(result, expected)

    @patch('watchmen.models.spectre.datetime')
    def test_get_s3_filename(self, mock_datetime):
        """
        test watchmen.models.spectre:: Spectre :: _get_s3_filename
        """
        spectre_obj = Spectre()
        mock_datetime.now.return_value = self.example_today
        expected_result = self.example_filename
        returned_result = spectre_obj._create_s3_filename()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.models.spectre.Spectre._check_if_found_file')
    @patch('watchmen.models.spectre.Spectre._create_message')
    def test_monitor(self, mock_message, mock_found):
        """
        test watchmen.models.spectre:: Spectre :: monitor
        """
        spectre_obj = Spectre()
        mock_message.return_value = self.example_message_chart.get(False)
        mock_found.return_value = False, "string"
        expected = self.example_result_dict
        result = spectre_obj.monitor().to_dict()

        # since spectre does not give observed time, we don't test the time here
        result['observed_time'] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(result, expected)
