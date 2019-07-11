import unittest
from datetime import datetime
from mock import patch
import pytz

from watchmen.models.moloch import Moloch


class TestMoloch(unittest.TestCase):

    def setUp(self):
        self.example_filename = "/2019/12/18/ZMQ_Output_"
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_file_path = 'somepath/to/a/file'
        self.example_exception_message = "Something is not working"
        self.example_message_chart = {
            "exception": "The newly observed domain feeds and hostname "
                         "feeds reached an exception during the file checking "
                         "process due to the following:\n\n{}\n\nPlease look at the logs for more insight.",
            "fail_domain": "ERROR: The newly observed hostname feed has gone down! "
                           "To view missing data go run the command "
                           "aws s3 ls s3://deteque-new-observable-data/NewlyObservedDomains "
                           "and head towards the most recent data. Afterwards contact Devops "
                           "team to restart Domains tasks in AWS SaaS account.",
            "fail_hostname": "ERROR: The newly observed domains feed has gone down! "
                             "To view missing data go run the command aws s3 ls "
                             "s3://deteque-new-observable-data/NewlyObservedHostname and head towards "
                             "the most recent data. Afterwards contact Devops team to restart Hostname "
                             "tasks in AWS SaaS account.",
            "fail_both": "ERROR: Both hostname and domains feed have gone down! "
                         "To view missing data go run the command aws s3 ls "
                         "s3://deteque-new-observable-data/NewlyObservedHostname and run the "
                         "command s3 ls s3://deteque-new-observable-data/NewlyObservedDomains  head towards "
                         "the most recent data. Afterwards contact Devops team to restart Hostname "
                         "and Domains tasks in AWS SaaS account.",
            "success": "NOH/D Feeds are up and running!",
        }
        self.example_result_dict = {
            "details": {},
            "disable_notifier": False,
            "message": self.example_message_chart.get("fail_both"),
            "observed_time": "2018-12-18T00:00:00+00:00",
            "result_id": 0,
            "success": False,
            "source": "Moloch",
            "state": "FAILURE",
            "subject": "Moloch neustar data monitor detected a failure!",
            "target": "Neustar",
        }

    # @mock_s3
    @patch('watchmen.models.moloch.validate_file_on_s3')
    def test_check_for_existing_files(self, mock_validate_file):
        """
        test watchmen.models.moloch :: Moloch :: _check_for_existing_files
        """
        moloch_obj = Moloch()
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

    @patch('watchmen.models.moloch.Moloch._check_for_existing_files')
    def test_get_check_results(self, mock_check):
        """
        test watchmen.models.moloch :: Moloch :: _get_check_results
        """
        moloch_obj = Moloch()
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
            expected = domain, hostname
            returned = moloch_obj._get_check_results()
            self.assertEqual(expected, returned)
