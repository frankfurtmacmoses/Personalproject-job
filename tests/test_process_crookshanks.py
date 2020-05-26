import pytz
import unittest
from datetime import datetime, timedelta
from mock import patch

from watchmen.process.crookshanks import Crookshanks
from watchmen.process.crookshanks import MESSAGES


class TestCrookshanks(unittest.TestCase):

    def setUp(self):
        self.check_time = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_time = self.check_time - timedelta(days=1)
        self.example_date = self.example_time.strftime('%Y%m%d')
        self.example_year = self.example_time.strftime('%Y')
        self.example_fail_string = "stuff#1"
        self.example_except_string = "stuff#3\n\n"
        self.fail_check_results = {
            "subject": MESSAGES.get("failure_subject"),
            "details": MESSAGES.get("failure_message").format(self.example_fail_string),
            "log_messages": MESSAGES.get("log_failure_message").format(self.example_fail_string)
        }
        self.example_failure_parameters = {
            "success": False,
            "disable_notifier": False,
            "state": "FAILURE",
            "details": MESSAGES.get("failure_message").format(self.example_fail_string),
            "target": "Smartlisting",
            "subject": MESSAGES.get("failure_subject"),
            "message": MESSAGES.get("log_failure_message").format(self.example_fail_string)
        }
        self.example_failure_result = {
            "details": MESSAGES.get("failure_message").format(self.example_fail_string),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            'is_notified': False,
            "message": MESSAGES.get("log_failure_message").format(self.example_fail_string),
            "result_id": 0,
            "snapshot": None,
            "source": "Crookshanks",
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": "Smartlisting"
        }
        self.failure_scenarios = {
            "failures": ["stuff#1"],
            "exceptions": []
        }

    @patch('watchmen.process.crookshanks.validate_file_on_s3')
    def test_check_s3_files(self, mock_validate):
        crookshanks_obj = Crookshanks(event=None, context=None)
        tests = [
            {
                "validate_value": [True, True, True, True, True],
                "False": 0
            }, {
                "validate_value": [False, True, True, True, True],
                "False": 1
            }, {
                "validate_value": [False, False, True, True, True],
                "False": 2
            }, {
                "validate_value": [False, False, False, True, True],
                "False": 3
            }, {
                "validate_value": [False, False, False, False, True],
                "False": 4
            }, {
                "validate_value": [False, False, False, False, False],
                "False": 5
            }
        ]
        for test in tests:
            mock_validate.side_effect = test.get("validate_value")
            expected = test.get("False")
            returned = crookshanks_obj.check_s3_files()
            failure_returned = len(returned.get("failures"))
            self.assertEqual(expected, failure_returned)

    @patch('watchmen.process.crookshanks.validate_file_on_s3')
    @patch('watchmen.process.crookshanks.traceback.format_exc')
    def test_check_s3_files_exception(self, mock_traceback, mock_validate):
        example_exception_msg = "Something is broken"
        traceback = "Traceback was created"
        expected_scenario = {
                "failures": [],
                "exceptions": [{"atc": traceback}, {"farsight": traceback}, {"majestic": traceback},
                               {"nios": traceback}, {"umbrella": traceback}]
            }
        crookshanks_obj = Crookshanks(event=None, context=None)
        mock_validate.side_effect = Exception(example_exception_msg)
        mock_traceback.return_value = traceback
        results = crookshanks_obj.check_s3_files()
        self.assertEqual(expected_scenario, results)

    def test_create_details(self):
        crookshanks_obj = Crookshanks(event=None, context=None)
        failure_except_scenarios = {
            "failures": ["stuff#1"],
            "exceptions": ["stuff#3"]
        }
        except_scenarios = {
            "failures": [],
            "exceptions": ["stuff#3"]
        }
        success_scenarios = {
            "failures": [],
            "exceptions": []
        }
        fail_except_check_results = {
            "subject": MESSAGES.get("failure_exception_subject"),
            "details": MESSAGES.get("failure_exception_message").format(self.example_fail_string,
                                                                        self.example_except_string),
            "log_messages": MESSAGES.get("log_fail_exception_msg").format(self.example_fail_string,
                                                                          self.example_except_string)
        }
        except_check_results = {
            "subject": MESSAGES.get("exception_subject"),
            "details": MESSAGES.get("exception_message").format(self.example_except_string),
            "log_messages": MESSAGES.get("log_exception_message").format(self.example_except_string)
        }
        success_check_results = {
            "subject": "SUCCESS: All expected smartlisting files exists in S3!",
            "details": MESSAGES.get("success_message"),
            "log_messages": MESSAGES.get("success_message")
        }
        tests = [
            {"scenario": failure_except_scenarios,
             "expected_value": False,
             "expected_msg": fail_except_check_results},
            {"scenario": self.failure_scenarios,
             "expected_value": False,
             "expected_msg": self.fail_check_results},
            {"scenario": except_scenarios,
             "expected_value": None,
             "expected_msg": except_check_results},
            {"scenario": success_scenarios,
             "expected_value": True,
             "expected_msg": success_check_results
             }]

        for test in tests:
            scenario = test.get("scenario")
            expected_details = test.get("expected_msg")
            expected_value = test.get("expected_value")
            returned_value, returned_details = crookshanks_obj.create_details(scenario)
            self.assertEqual(expected_details, returned_details)
            self.assertEqual(expected_value, returned_value)

    @patch('watchmen.process.crookshanks.datetime')
    def test_create_full_path(self, mock_datetime):
        crookshanks_obj = Crookshanks(event=None, context=None)
        example_source = "atc"
        example_file_name = "smartlist_{}_atc.csv"
        example_path_prefix = "whitelist/smartlisting/prod/smartlist/src=atc/year={}/"
        mock_datetime.utcnow.return_value = self.check_time
        expected = example_path_prefix.format(self.example_year)+example_file_name.format(self.example_date)
        returned = crookshanks_obj.create_full_path(example_source)
        self.assertEqual(expected, returned)

    def test_create_result(self):
        crookshanks_obj = Crookshanks(event=None, context=None)
        expected = self.example_failure_result
        returned = crookshanks_obj.create_result(self.example_failure_parameters).to_dict()
        returned['dt_created'] = "2018-12-18T00:00:00+00:00"
        returned['dt_updated'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, returned)

    def test_create_result_parameters(self):
        crookshanks_obj = Crookshanks(event=None, context=None)
        expected = self.example_failure_parameters
        returned = crookshanks_obj.create_result_parameters(self.fail_check_results, False)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.crookshanks.Crookshanks.check_s3_files')
    @patch('watchmen.process.crookshanks.Crookshanks.create_details')
    def test_monitor(self, mock_details, mock_check_files):
        crookshanks_obj = Crookshanks(event=None, context=None)
        mock_check_files.return_value = self.failure_scenarios
        mock_details.return_value = False, self.fail_check_results
        expected = self.example_failure_result
        returned = crookshanks_obj.monitor()[0].to_dict()

        returned['dt_created'] = "2018-12-18T00:00:00+00:00"
        returned['dt_updated'] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, returned)
