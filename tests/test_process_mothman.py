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
            "generic_example": [
                {
                    "latest_file_path": "latest_file_s3_path",
                    "latest_hour_minute": "1450",
                    "previous_file_path": "previous_file_s3_path",
                    "previous_hour_minute": "1440"
                }
            ],
            "latest_file_0000": [
                {
                    "latest_file_path": "latest_file_s3_path",
                    "latest_hour_minute": "0000",
                    "previous_file_path": "previous_file_s3_path",
                    "previous_hour_minute": "2350"
                }
            ],
            "latest_file_dne": [
                {
                    "latest_file_path": "bad_path",
                    "latest_hour_minute": "1450",
                    "previous_file_path": "previous_file_s3_path",
                    "previous_hour_minute": "1440"
                }
            ],
            "previous_file_0000": [
                {
                    "latest_file_path": "latest_file",
                    "latest_hour_minute": "0010",
                    "previous_file_path": "previous_file_s3_path",
                    "previous_hour_minute": "0000"
                }
            ],
            "previous_file_dne": [
                {
                    "latest_file_path": "latest_file_s3_path",
                    "latest_hour_minute": "1450",
                    "previous_file_path": "bad_path",
                    "previous_hour_minute": "1440"
                }
            ]
        }
        self.latest_time = "2019-12-15-12-20"
        self.parameters = {
            "details": self.details + '\n\n',
            "disable_notifier": True,
            "short_message": MESSAGES.get("success_short_message"),
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": "Malspam MTA"
        }
        self.previous_time = "2019-12-15-12-10"
        self.result_dict = {
            "details": self.details + '\n\n',
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message"),
            "watchman_name": "Mothman",
            "result_id": 0,
            "snapshot": {},
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": "Malspam MTA",
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
        tests = [
            {
                "check_unequal_files": [True, True],
                "get_key": ["existing_object", "existing_object", "existing_object", "existing_object"],
                "files_info": [
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0010",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "0000"
                    },
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0020",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "0010"
                    },
                ],
                "expected": [
                    {
                        "success": True,
                        "details": MESSAGES.get("success_previous_hm")
                    },
                    {
                        "success": True,
                        "details": MESSAGES.get("success_unequal_files").format(
                            "latest_file_s3_path", "previous_file_s3_path"
                        )
                    }
                ]
            },
            {
                "check_unequal_files": [False, True],
                "get_key": ["existing_object", "existing_object", None, "existing_object"],
                "files_info": [
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0020",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "0010"
                    },
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0020",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "0010"
                    },
                ],
                "expected": [
                    {
                        "success": False,
                        "details": MESSAGES.get("failure_equal_files").format(
                            "latest_file_s3_path", "previous_file_s3_path"
                        )
                    },
                    {
                        "success": False,
                        "details": MESSAGES.get("failure_latest_file_dne").format("latest_file_s3_path")
                    }
                ]
            },
            {
                "check_unequal_files": [False, True],
                "get_key": ["existing_object", None, "existing_object", "existing_object"],
                "files_info": [
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0000",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "2350"
                    },
                    {
                        "latest_file_path": "latest_file_s3_path",
                        "latest_hour_minute": "0020",
                        "previous_file_path": "previous_file_s3_path",
                        "previous_hour_minute": "0010"
                    },
                ],
                "expected": [
                    {
                        "success": True,
                        "details": MESSAGES.get("success_latest_hm").format("latest_file_s3_path")
                    },
                    {
                        "success": True,
                        "details": MESSAGES.get("success_previous_file_dne").format("previous_file_s3_path")
                    }
                ]
            },
        ]
        for test in tests:
            mothman_obj = self._create_mothman_obj()
            mock_check_unequal.side_effect = test['check_unequal_files']
            mock_get_key.side_effect = test['get_key']
            returned = mothman_obj._check_s3_files(test['files_info'])
            self.assertEqual(test['expected'], returned)

    @patch('watchmen.process.mothman.get_key')
    @patch('watchmen.process.mothman.traceback.format_exc')
    def test_check_s3_files_exception(self, mock_traceback, mock_get_key):
        traceback = "Traceback created during exception catch."
        mock_get_key.side_effect = Exception()
        mock_traceback.return_value = traceback
        mothman_obj = self._create_mothman_obj()
        expected = [
            {"success": None, "details": MESSAGES.get("exception_details").format(traceback)}
        ]
        file_check_info = mothman_obj._check_s3_files(self.file_info_examples.get("generic_example"))
        self.assertEqual(expected, file_check_info)

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
        tests = [
            {
                'expected': [
                    {
                        "latest_file_path": "malspam/forevermail/2019/12/15/12/1220.tar.gz",
                        "latest_hour_minute": "1220",
                        "previous_file_path": "malspam/forevermail/2019/12/15/12/1210.tar.gz",
                        "previous_hour_minute": "1210"
                    },
                    {
                        "latest_file_path": "malspam/uscert/2019/12/15/12/1220.tar.gz",
                        "latest_hour_minute": "1220",
                        "previous_file_path": "malspam/uscert/2019/12/15/12/1210.tar.gz",
                        "previous_hour_minute": "1210"
                    }
                ]
            }
        ]
        mock_get_times.return_value = self.previous_time, self.latest_time
        mothman_obj = self._create_mothman_obj()
        for test in tests:
            returned = mothman_obj._create_paths_info()
            self.assertEqual(test['expected'], returned)

    def test_create_result(self):
        tests = [
            {
                'expected': self.result_dict,
                'dt_created': "2018-12-18T00:00:00+00:00"
            }
        ]
        mothman_obj = self._create_mothman_obj()
        for test in tests:
            returned = mothman_obj._create_result(self.parameters).to_dict()
            returned['dt_created'] = test['dt_created']
            self.assertEqual(test['expected'], returned)

    def test_create_result_parameters(self):
        tests = [
            {
                'expected': self.parameters,
                'files_check_info': [{"success": True, "details": self.details}]
            }
        ]
        mothman_obj = self._create_mothman_obj()
        for test in tests:
            returned = mothman_obj._create_result_parameters(test['files_check_info'])
            self.assertEqual(test['expected'], returned)

    @patch('watchmen.process.mothman.datetime')
    def test_get_times_to_check(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(year=2019, month=12, day=15, hour=12, minute=30, tzinfo=pytz.utc)
        mothman_obj = self._create_mothman_obj()

        expected = self.previous_time, self.latest_time
        returned = mothman_obj._get_times_to_check()

        self.assertEqual(expected, returned)

    @patch('watchmen.process.mothman.Mothman._create_paths_info')
    @patch('watchmen.process.mothman.Mothman._check_s3_files')
    def test_monitor(self, mock_check_s3, mock_create_path):
        tests = [
            {
                'files_info': self.file_info_examples.get("generic_example"),
                's3_checks': [
                    {"success": True, "tb": None, "details": self.details},
                ],
                'expected': self.result_dict,
                'dt_created': "2018-12-18T00:00:00+00:00"
            }
        ]
        mothman_obj = self._create_mothman_obj()
        for test in tests:
            mock_create_path.return_value = test['files_info']
            mock_check_s3.return_value = test['s3_checks']
            returned = mothman_obj.monitor()[0].to_dict()
            returned['dt_created'] = test['dt_created']
            self.assertEqual(test['expected'], returned)
