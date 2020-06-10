import unittest
from datetime import datetime
from mock import patch
import pytz

from watchmen.process.moloch import Moloch


class TestMoloch(unittest.TestCase):

    def setUp(self):
        self.example_filename = "/2019/12/18/ZMQ_Output_"
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_file_path = "somepath/to/a/file"
        self.example_exception_details = "Something is not working"
        self.error = "ERROR: "
        self.failure_domain_start = self.error + "The newly observed domains feed has gone down!"
        self.failure_hostname_start = self.error + "The newly observed hostname feed has gone down!"
        self.failure_both_start = self.error + "Both hostname and domains feed have gone down!"
        self.failure_general_details = "{}\nPlease check the Response Guide for Moloch in watchmen documents: " \
                                       "https://docs.google.com/document/d/1to0ZIaU4E-XRbZ8QvNrPLe4" \
                                       "30bWWxRAPCkWk68pcwjE/edit#heading=h.6dcje1sj7gup"
        self.example_details_chart = {
            "exception": "The newly observed domain feeds and hostname "
                         "feeds reached an exception during the file checking "
                         "process due to the following:\n\n{}\n\nPlease look at the logs for more insight.",
            "fail_domain": self.failure_general_details.format(self.failure_domain_start),
            "fail_hostname": self.failure_general_details.format(self.failure_hostname_start),
            "fail_both": self.failure_general_details.format(self.failure_both_start),
            "success": "NOH/D Feeds are up and running!",
        }
        self.example_result_dict = {
            "details": "ERROR: Both hostname and domains feed have gone down!\n"
                       "Please check the Response Guide for Moloch in watchmen documents: "
                       "https://docs.google.com/document/d/1to0ZIaU4E-XRbZ8QvNrPLe430bWWxR"
                       "APCkWk68pcwjE/edit#heading=h.6dcje1sj7gup",
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": "Moloch: A Feed has gone down, please check logs in CloudWatch!",
            "result_id": 0,
            "snapshot": None,
            "watchman_name": "Moloch",
            "state": "FAILURE",
            "subject": "Moloch watchmen detected an issue with NOH/D feed!",
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
            "result": self.example_details_chart.get("fail_hostname"),
            "msg_type": False,
        }, {
            "hostname_check": True,
            "domain_check": False,
            "result": self.example_details_chart.get("fail_domain"),
            "msg_type": False,
        }, {
            "hostname_check": False,
            "domain_check": False,
            "result": self.example_details_chart.get("fail_both"),
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
            "Moloch: A Feed has gone down, please check logs in CloudWatch!",
            False,
            False,
            "FAILURE",
            "Moloch watchmen detected an issue with NOH/D feed!",
            self.example_details_chart.get("fail_both")).to_dict()
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
        mock_create_details.return_value = self.example_details_chart.get("fail_both"), False
        mock_get_check.return_value = False, False, "string"
        expected = self.example_result_dict
        result = moloch_obj.monitor()[0].to_dict()

        # since moloch does not give observed time, we don't test the time here
        result["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.maxDiff = None
        self.assertDictEqual(result, expected)
