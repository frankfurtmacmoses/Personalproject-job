import unittest
from datetime import datetime
import pytz

from mock import patch
from watchmen.process.spectre import Spectre


class TestSpectre(unittest.TestCase):

    def setUp(self):
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_filename = "2018/12/gt_mpdns_20181217.zip"
        self.example_exception_details = "Something is not working"
        self.example_status = "The file was checked"
        self.example_details_chart = {
            None: 'Spectre for Georgia Tech failed '
                  'on \n\t"2018/12/gt_mpdns_20181217.zip" \ndue to '
                  'the Exception:\n\n{}\n\nPlease check the logs!',
            False: "ERROR: 2018/12/gt_mpdns_20181217.zip "
                   "could not be found in cyber-intel/hancock/georgia_tech/! "
                   "Please check S3 and Georgia Tech logs!",
            True: "Georgia Tech Feed data found on S3!",
        }
        self.example_result_dict = {
            "details": "ERROR: 2018/12/gt_mpdns_20181217.zip could not be found in "
                       "cyber-intel/hancock/georgia_tech/! Please check S3 and Georgia "
                       "Tech logs!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": None,
            "source": "Spectre",
            "state": "FAILURE",
            "subject": "Spectre Georgia Tech data monitor detected a failure!",
            "success": False,
            "target": "Georgia Tech S3",
        }

    @patch('watchmen.process.spectre.validate_file_on_s3')
    def test_check_if_found_file(self, mock_validate):
        """
        test watchmen.process.spectre:: Spectre :: _check_if_found_file
        """
        spectre_obj = Spectre(event=None, context=None)
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
        mock_validate.side_effect = Exception(self.example_exception_details)
        result, result_tb = spectre_obj._check_if_found_file(self.example_filename)
        self.assertEqual(result, None)
        self.assertTrue(self.example_exception_details in result_tb)

    def test_create_details(self):
        """
        test watchmen.process.spectre:: Spectre :: _create_details
        """
        file_founds = [True, False, None]
        spectre_obj = Spectre(event=None, context=None)
        for file_found in file_founds:
            expected = self.example_details_chart.get(file_found)
            result = spectre_obj._create_details(self.example_filename, file_found, {})
            self.assertEqual(result, expected)

    def test_create_result(self):
        """
        test watchmen.process.spectre:: Spectre :: _create_result
        """
        expected = self.example_result_dict
        spectre_obj = Spectre(event=None, context=None)
        result = spectre_obj._create_result(
            False,
            False,
            "FAILURE",
            "Spectre Georgia Tech data monitor detected a failure!",
            self.example_details_chart.get(False)).to_dict()
        # since spectre does not give observed time, we don't test the time here
        result['dt_created'] = "2018-12-18T00:00:00+00:00"
        result['dt_updated'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(result, expected)

    @patch('watchmen.process.spectre.datetime')
    def test_get_s3_filename(self, mock_datetime):
        """
        test watchmen.process.spectre:: Spectre :: _get_s3_filename
        """
        spectre_obj = Spectre(event=None, context=None)
        mock_datetime.now.return_value = self.example_today
        expected_result = self.example_filename
        returned_result = spectre_obj._create_s3_filename()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.spectre.Spectre._check_if_found_file')
    @patch('watchmen.process.spectre.Spectre._create_details')
    def test_monitor(self, mock_details, mock_found):
        """
        test watchmen.process.spectre:: Spectre :: monitor
        """
        spectre_obj = Spectre(event=None, context=None)
        mock_details.return_value = self.example_details_chart.get(False)
        mock_found.return_value = False, "string"
        expected = self.example_result_dict
        result = spectre_obj.monitor()[0].to_dict()

        # since spectre does not give observed time, we don't test the time here
        result['dt_created'] = "2018-12-18T00:00:00+00:00"
        result['dt_updated'] = "2018-12-18T00:00:00+00:00"

        self.assertDictEqual(result, expected)
