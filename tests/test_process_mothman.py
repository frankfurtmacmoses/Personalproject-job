import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen.process.mothman import Mothman
from watchmen.process.mothman import MESSAGES


class TestMothman(unittest.TestCase):

    def setUp(self):
        self.details = "Example details returned from _check_s3_files"
        self.file_info_examples = {
            "generic_example": {
                "latest_file_path": "latest_file_s3_path",
                "latest_hour_minute": "1450",
                "previous_file_path": "previous_file_s3_path",
                "previous_hour_minute": "1440"
            },
            "latest_file_0000": {
                "latest_file_path": "latest_file_s3_path",
                "latest_hour_minute": "0000",
                "previous_file_path": "previous_file_s3_path",
                "previous_hour_minute": "2350"
            },
            "latest_file_dne": {
                "latest_file_path": "bad_path",
                "latest_hour_minute": "1450",
                "previous_file_path": "previous_file_s3_path",
                "previous_hour_minute": "1440"
            },
            "previous_file_0000": {
                "latest_file_path": "latest_file",
                "latest_hour_minute": "0010",
                "previous_file_path": "previous_file_s3_path",
                "previous_hour_minute": "0000"
            },
            "previous_file_dne": {
                "latest_file_path": "latest_file_s3_path",
                "latest_hour_minute": "1450",
                "previous_file_path": "bad_path",
                "previous_hour_minute": "1440"
            }

        }
        self.latest_time = "2019-12-15-12-20"
        self.parameters = {
            "details": self.details,
            "disable_notifier": True,
            "short_message": MESSAGES.get("success_short_message"),
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": "ForeverMail"
        }
        self.previous_time = "2019-12-15-12-10"
        self.result_dict = {
            "details": self.details,
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message"),
            "watchman_name": "Mothman",
            "result_id": 0,
            "snapshot": {},
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": "ForeverMail",
        }

    @staticmethod
    def _create_mothman_obj():
        """
        Creates a Mothman object.
        @return: <Mothman> object.
        """
        return Mothman(event=None, context=None)

    @patch('watchmen.process.mothman.get_key')
    @patch('watchmen.process.mothman.check_unequal_files')
    def test_check_s3_files(self, mock_check_unequal, mock_get_key):
        monitor_tests = [
            {
                "check_unequal_mock": None,
                "expected_details": MESSAGES.get("success_latest_hm").format(self.file_info_examples.
                                                                             get("latest_file_0000").
                                                                             get("latest_file_path")),
                "expected_success": True,
                "file_info": self.file_info_examples.get("latest_file_0000"),
                "get_key_mock": ["existing_object", "existing_object"]
            },
            {
                "check_unequal_mock": None,
                "expected_details": MESSAGES.get("failure_latest_file_dne").format(self.file_info_examples.
                                                                                   get("latest_file_dne").
                                                                                   get("latest_file_path")),
                "expected_success": False,
                "file_info": self.file_info_examples.get("latest_file_dne"),
                "get_key_mock": [None, "existing_object"]
            },
            {
                "check_unequal_mock": None,
                "expected_details": MESSAGES.get("success_previous_hm"),
                "expected_success": True,
                "file_info": self.file_info_examples.get("previous_file_0000"),
                "get_key_mock": ["existing_object", "existing_object"]
            },
            {
                "check_unequal_mock": None,
                "expected_details": MESSAGES.get("success_previous_file_dne").format(self.file_info_examples.
                                                                                     get("previous_file_dne").
                                                                                     get("previous_file_path")),
                "expected_success": True,
                "file_info": self.file_info_examples.get("previous_file_dne"),
                "get_key_mock": ["existing_object", None]
            },
            {
                "check_unequal_mock": True,
                "expected_details": MESSAGES.get("success_unequal_files").format(self.file_info_examples.
                                                                                 get("generic_example").
                                                                                 get("latest_file_path"),
                                                                                 self.file_info_examples.
                                                                                 get("generic_example").
                                                                                 get("previous_file_path")),
                "expected_success": True,
                "file_info": self.file_info_examples.get("generic_example"),
                "get_key_mock": ["existing_object", "existing_object"]
            },
            {
                "check_unequal_mock": False,
                "expected_details": MESSAGES.get("failure_equal_files").format(self.file_info_examples.
                                                                               get("generic_example").
                                                                               get("latest_file_path"),
                                                                               self.file_info_examples.
                                                                               get("generic_example").
                                                                               get("previous_file_path")),
                "expected_success": False,
                "file_info": self.file_info_examples.get("generic_example"),
                "get_key_mock": ["existing_object", "existing_object"]
            },
        ]

        for test in monitor_tests:
            check_unequal_mock = test.get("check_unequal_mock")
            expected_details = test.get("expected_details")
            expected_success = test.get("expected_success")
            file_info = test.get("file_info")
            get_key_mock = test.get("get_key_mock")
            mock_get_key.side_effect = get_key_mock
            mock_check_unequal.return_value = check_unequal_mock

            mothman_obj = self._create_mothman_obj()
            file_check_info = mothman_obj._check_s3_files(file_info)
            self.assertEqual(expected_details, file_check_info.get("details"))
            self.assertEqual(expected_success, file_check_info.get("success"))

    @patch('watchmen.process.mothman.get_key')
    @patch('watchmen.process.mothman.traceback.format_exc')
    def test_check_s3_files_exception(self, mock_traceback, mock_get_key):
        traceback = "Traceback created during exception catch."
        mock_get_key.side_effect = Exception()
        mock_traceback.return_value = traceback
        mothman_obj = self._create_mothman_obj()

        expected_success = None
        expected_details = MESSAGES.get("exception_details").format(traceback)
        file_check_info = mothman_obj._check_s3_files(self.file_info_examples.get("generic_example"))

        self.assertEqual(expected_details, file_check_info.get("details"))
        self.assertEqual(expected_success, file_check_info.get("success"))

    def test_convert_datetime_to_dict(self):
        datetime_string = "2019-12-15-05-05"
        time_info = {
            "year": "2019",
            "month": "12",
            "day": "15",
            "hour": "05",
            "minute": "00",
        }
        mothman_obj = self._create_mothman_obj()

        expected = time_info
        returned = mothman_obj._convert_datetime_to_dict(datetime_string)

        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.Mothman._get_times_to_check')
    def test_create_path_info(self, mock_get_times):
        path_info = {
            "latest_file_path": "malspam/forevermail/2019/12/15/12/1220.tar.gz",
            "latest_hour_minute": "1220",
            "previous_file_path": "malspam/forevermail/2019/12/15/12/1210.tar.gz",
            "previous_hour_minute": "1210"
        }
        mock_get_times.return_value = self.previous_time, self.latest_time
        mothman_obj = self._create_mothman_obj()

        expected = path_info
        returned = mothman_obj._create_path_info()

        self.assertEqual(expected, returned)

    def test_create_result(self):
        mothman_obj = self._create_mothman_obj()

        expected = self.result_dict
        returned = mothman_obj._create_result(self.parameters).to_dict()
        returned["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, returned)

    def test_create_result_parameters(self):
        mothman_obj = self._create_mothman_obj()

        expected = self.parameters
        returned = mothman_obj._create_result_parameters(True, self.details)

        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.datetime')
    def test_get_times_to_check(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(year=2019, month=12, day=15, hour=12, minute=30, tzinfo=pytz.utc)
        mothman_obj = self._create_mothman_obj()

        expected = self.previous_time, self.latest_time
        returned = mothman_obj._get_times_to_check()

        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.Mothman._create_path_info')
    @patch('watchmen.process.mothman.Mothman._check_s3_files')
    def test_monitor(self, mock_check_s3, mock_create_path):
        mock_create_path.return_value = self.file_info_examples.get("generic_example")
        mock_check_s3.return_value = {"success": True, "tb": None, "details": self.details}
        mothman_obj = self._create_mothman_obj()

        expected = self.result_dict
        returned = mothman_obj.monitor()[0].to_dict()
        returned["dt_created"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected, returned)
