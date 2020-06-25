import unittest
from datetime import datetime
from mock import patch
import pytz

from watchmen.process.moloch import Moloch
from watchmen.process.moloch import MESSAGES


class TestMoloch(unittest.TestCase):

    def setUp(self):
        self.example_filename = "/2019/12/18/ZMQ_Output_"
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_file_path = "somepath/to/a/file"
        self.example_exception_details = "Something is not working"
        self.example_details_chart = {
            "exception": MESSAGES.get("exception_message"),
            "failure_domain": MESSAGES.get("failure_domain"),
            "failure_hostname": MESSAGES.get("failure_hostname"),
            "failure_both": MESSAGES.get("failure_both"),
            "success": MESSAGES.get("success_message"),
        }
        self.example_result_dict = {
            "details": MESSAGES.get("failure_both"),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("failure_short_message"),
            "result_id": 0,
            "snapshot": None,
            "watchman_name": "Moloch",
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": "Newly Observed Data",
        }

    # @mock_s3
    @patch('watchmen.process.moloch.validate_file_on_s3')
    def test_check_for_existing_files(self, mock_validate_file):
        """
        test watchmen.process.moloch :: Moloch :: _check_for_existing_files
        """
        moloch_obj = Moloch(event=None, context=None)
        tests = [{
            "side_effects": [True, False, True, False],
            "result": True,
        }, {
            "side_effects": [True, True, True],
            "result": True,
        }, {
            "side_effects": [False, True, False, False],
            "result": True,
        }, {
            "side_effects": [True, False, False, False],
            "result": True,
        }, {
            "side_effects": [True],
            "result": True,
        }, {
            "side_effects": [False] * 60,
            "result": False,
        }, {
            "side_effects": [False] * 59 + [True],
            "result": True,
        }]
        for test in tests:
            mock_validate_file.side_effect = test.get("side_effects")
            expected = test.get("result")
            result = moloch_obj._check_for_existing_files(self.example_filename, self.example_today)
            self.assertEqual(expected, result)
        pass

    @patch('watchmen.process.moloch.Moloch._check_for_existing_files')
    def test_get_check_results(self, mock_check):
        """
        test watchmen.process.moloch :: Moloch :: _get_check_results
        """
        moloch_obj = Moloch(event=None, context=None)
        test_results = [
            {"domain": True, "hostname": True},
            {"domain": False, "hostname": True},
            {"domain": True, "hostname": False},
            {"domain": False, "hostname": False}
        ]

        for results in test_results:
            domain = results.get("domain")
            hostname = results.get("hostname")
            mock_check.side_effect = [domain, hostname]
            expected = (domain, hostname, None)
            returned = moloch_obj._get_check_results()
            self.assertEqual(expected, returned)

        # Exception occurred
        mock_check.side_effect = Exception(self.example_exception_details)
        returned_domain, returned_hostname, returned_tb = moloch_obj._get_check_results()
        self.assertEqual((returned_domain, returned_hostname), (None, None))
        self.assertTrue(self.example_exception_details in returned_tb)

    def test_create_details(self):
        """
        test watchmen.process.moloch :: Moloch :: _create_details
        """
        moloch_obj = Moloch(event=None, context=None)
        tests = [{
            "hostname_check": True,
            "domain_check": True,
            "result": self.example_details_chart.get("success"),
            "msg_type": True,
        }, {
            "hostname_check": False,
            "domain_check": True,
            "result": self.example_details_chart.get("failure_hostname"),
            "msg_type": False,
        }, {
            "hostname_check": True,
            "domain_check": False,
            "result": self.example_details_chart.get("failure_domain"),
            "msg_type": False,
        }, {
            "hostname_check": False,
            "domain_check": False,
            "result": self.example_details_chart.get("failure_both"),
            "msg_type": False,
        }, {
            "hostname_check": None,
            "domain_check": False,
            "result": self.example_details_chart.get("exception"),
            "msg_type": None,
        }, {
            "hostname_check": False,
            "domain_check": None,
            "result": self.example_details_chart.get("exception"),
            "msg_type": None,
        }, {
            "hostname_check": True,
            "domain_check": None,
            "result": self.example_details_chart.get("exception"),
            "msg_type": None,
        }, {
            "hostname_check": None,
            "domain_check": True,
            "result": self.example_details_chart.get("exception"),
            "msg_type": None,
        }, {
            "hostname_check": None,
            "domain_check": None,
            "result": self.example_details_chart.get("exception"),
            "msg_type": None,
        }]

        for test in tests:
            hostname_check = test.get("hostname_check")
            domain_check = test.get("domain_check")
            expected = test.get("result")
            expected_msg_type = test.get("msg_type")
            result, msg_type = moloch_obj._create_details(hostname_check, domain_check, {})
            self.assertEqual(expected, result)
            self.assertEqual(expected_msg_type, msg_type)

    def test_create_result(self):
        """
        test watchmen.process.moloch:: Moloch :: _create_result
        """
        expected = self.example_result_dict
        moloch_obj = Moloch(event=None, context=None)
        result = moloch_obj._create_result(
            MESSAGES.get("failure_short_message"),
            False,
            False,
            "FAILURE",
            MESSAGES.get("failure_subject"),
            self.example_details_chart.get("failure_both")).to_dict()
        # since moloch does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, result)

    @patch('watchmen.process.moloch.Moloch._get_check_results')
    @patch('watchmen.process.moloch.Moloch._create_details')
    def test_monitor(self, mock_create_details, mock_get_check):
        """
        test watchmen.process.moloch:: Moloch :: monitor
        """
        moloch_obj = Moloch(event=None, context=None)
        mock_create_details.return_value = self.example_details_chart.get("failure_both"), False
        mock_get_check.return_value = False, False, "string"
        expected = self.example_result_dict
        result = moloch_obj.monitor()[0].to_dict()

        # since moloch does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.maxDiff = None
        self.assertDictEqual(result, expected)
