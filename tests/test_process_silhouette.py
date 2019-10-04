import unittest
from datetime import datetime
import pytz

from mock import patch
from watchmen.process.silhouette import Silhouette


class TestSilhouette(unittest.TestCase):

    def setUp(self):
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_filename = "analytics/lookalike/prod/results/2018/12/16/status.json"
        self.example_exception_details = "Something is not working"
        self.example_details_chart = {
            None: 'Silhouette for lookalike feeds failed '
                  'on \n\t"analytics/lookalike/prod/results/2018/12/16/status.json" \ndue to '
                  'the Exception:\n\n{}\n\nPlease check the logs!',
            False: 'ERROR: analytics/lookalike/prod/results/2018/12/16/status.json'
                   'Lookalike feed never added files from 2 days ago! '
                   'The feed may be down or simply did not complete!',
            True: 'Lookalike feed is up and running!',
        }
        self.example_success_json = {"STATE": "COMPLETED"}
        self.example_failed_json = {"STATE": "UNCOMPLETED"}
        self.example_result_dict = {
            "details": "ERROR: "
                       "analytics/lookalike/prod/results/2018/12/16/status.jsonLookalike "
                       "feed never added files from 2 days ago! The feed may be down or "
                       "simply did not complete!",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": "NO MESSAGE",
            "result_id": 0,
            "snapshot": None,
            "source": "Silhouette",
            "state": "FAILURE",
            "subject": "Silhouette watchman detected an issue with lookalike feed!",
            "success": False,
            "target": "Lookalike Feed S3",
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
            False,
            False,
            "FAILURE",
            "Silhouette watchman detected an issue with lookalike feed!",
            self.example_details_chart.get(False)).to_dict()
        # since silhouette does not give observed time, we don't test the time here
        result['dt_created'] = "2018-12-18T00:00:00+00:00"
        result['dt_updated'] = "2018-12-18T00:00:00+00:00"

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
        result['dt_updated'] = "2018-12-18T00:00:00+00:00"

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
