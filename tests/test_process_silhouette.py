import unittest
from datetime import datetime
import pytz

from mock import patch
from watchmen.process.silhouette import Silhouette
from watchmen.process.silhouette import MESSAGES


class TestSilhouette(unittest.TestCase):

    def setUp(self):
        self.example_today = datetime(year=2020, month=6, day=16, tzinfo=pytz.utc)
        self.example_filename = "analytics/lookalike2/prod/status/year=2020/month=06/day=15/status.json"
        self.example_exception_details = "Something is not working"
        self.example_failure_message = MESSAGES.get("failure_message")
        self.example_details_chart = {
            None: 'Silhouette for lookalike2 algorithm failed '
                  'on \n\t"analytics/lookalike2/prod/status/year=2020/month=06/day=15/status.json" \ndue to '
                  'the Exception:\n\n{}\n\nPlease check the logs!',
            False: 'ERROR: analytics/lookalike2/prod/status/year=2020/month=06/day=15/status.json\n'
                   'Lookalike2 algorithm never added files yesterday! '
                   'The algorithm may be down or simply did not complete!',
            True: MESSAGES.get("success_message"),
        }
        self.example_success_json = {"state": "completed"}
        self.example_failed_json = {"state": "uncompleted"}
        self.example_result_dict = {
            "details": "ERROR: analytics/lookalike2/prod/status/year=2020/month=06/day=15/status.json\n"
                       "Lookalike2 algorithm never added files yesterday! The algorithm may be down or "
                       "simply did not complete!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": self.example_failure_message,
            "result_id": 0,
            "snapshot": None,
            "watchman_name": "Silhouette",
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": "Lookalike2 Algorithm S3",
        }
        pass

    def test_create_details(self):
        """
        test watchmen.process.silhouette :: Silhouette :: _create_details
        """
        is_valid_chart = [True, False, None]
        silhouette_obj = Silhouette(event=None, context=None)
        for is_valid in is_valid_chart:
            expected = self.example_details_chart.get(is_valid)
            result = silhouette_obj._create_details(self.example_filename, is_valid, {})
            self.assertEqual(expected, result)

    @patch('watchmen.process.silhouette.Silhouette._process_status')
    def test_check_process_status(self, mock_process_status):
        """
        test watchmen.process.silhouette :: Silhouette :: _check_process_status
        """
        silhouette_obj = Silhouette(event=None, context=None)
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
            mock_process_status.return_value = test.get("is_valid")
            result, tb = silhouette_obj._check_process_status()
            self.assertEqual(expected, result)
            self.assertEqual(expected_tb, tb)

        # Exception occurred
        mock_process_status.side_effect = Exception(self.example_exception_details)
        result, result_tb = silhouette_obj._check_process_status()
        self.assertEqual(result, None)
        self.assertTrue(self.example_exception_details in result_tb)

    def test_create_result(self):
        """
        test watchmen.process.silhouette:: Silhouette :: _create_result
        """
        expected = self.example_result_dict
        silhouette_obj = Silhouette(event=None, context=None)
        result = silhouette_obj._create_result(
            self.example_failure_message,
            False,
            False,
            "FAILURE",
            MESSAGES.get("failure_subject"),
            self.example_details_chart.get(False)).to_dict()
        # since silhouette does not give observed time, we don't test the time here
        result['dt_created'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, result)

    @patch('watchmen.process.silhouette.datetime')
    def test_get_file_name(self, mock_datetime):
        """
        test watchmen.process.silhouette :: Silhouette :: _get_file_name
        """
        silhouette_obj = Silhouette(event=None, context=None)
        mock_datetime.now.return_value = self.example_today
        expected_result = self.example_filename
        returned_result = silhouette_obj._get_file_name()
        self.assertEqual(expected_result, returned_result)

    @patch('watchmen.process.silhouette.Silhouette._check_process_status')
    @patch('watchmen.process.silhouette.Silhouette._create_details')
    def test_monitor(self, mock_create_details, mock_check_process_status):
        """
        test watchmen.process.silhouette:: Silhouette :: monitor
        """
        silhouette_obj = Silhouette(event=None, context=None)
        mock_create_details.return_value = self.example_details_chart.get(False)
        mock_check_process_status.return_value = False, "string"
        expected = self.example_result_dict
        result = silhouette_obj.monitor()[0].to_dict()

        # since silhouette does not give observed time, we don't test the time here
        result['dt_created'] = "2018-12-18T00:00:00+00:00"
        self.maxDiff = None
        self.assertDictEqual(result, expected)

    @patch('watchmen.process.silhouette.json.loads')
    @patch('watchmen.process.silhouette.get_file_contents_s3')
    def test_process_status(self, mock_get_contents, mock_json_loads):
        """
        test watchmen.process.silhouette :: Silhouette :: _process_status
        """
        silhouette_obj = Silhouette(event=None, context=None)
        tests = [{
            "json": self.example_success_json,
            "content": "content",
            "result": True,
        }, {
            "json": self.example_failed_json,
            "content": "content",
            "result": False,
        }, {
            "json": {},
            "content": "content",
            "result": False,
        }, {
            "json": self.example_success_json,
            "content": None,
            "result": False,
        }]
        for test in tests:
            mock_get_contents.return_value = test.get("content")
            mock_json_loads.return_value = test.get("json")
            expected = test.get("result")
            result = silhouette_obj._process_status()
            self.assertEqual(expected, result)
