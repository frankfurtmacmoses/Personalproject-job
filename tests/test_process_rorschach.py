import datetime
import pytz
import unittest

from dateutil.relativedelta import relativedelta
from mock import mock_open, patch

from watchmen import const
from watchmen.common.watchman import Watchman
from watchmen.process.rorschach import Rorschach, MESSAGES, CONFIG_NAME


class TestRorschach(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'Type': {'Daily': '15:00'}}
        self.example_event_hourly = {'Type': {'Hourly': '00'}}
        self.example_event_weekly = {'Type': {'Weekly': 'Mon,10:45'}}
        self.example_invalid_events = [
            {'Type': 'hourly'},
            {'Type': 'daily'},
            {'type': 'Hourly'},
            {'type': 'Daily'},
            {'': ''},
            {}
        ]
        self.example_config_path = '../watchmen/process/s3_config.yaml'
        self.example_traceback = 'Traceback'
        self.expected_invalid_event_email_result = {
            'details': MESSAGES.get("exception_invalid_event_details"),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'short_message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'watchman_name': 'Rorschach',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_invalid_event_subject"),
            'success': False,
            'target': 'Generic S3 atg'
        }
        self.expected_invalid_config_file_result = {
            'details': "Cannot load S3 targets from file: s3_targets_atg_test.yaml\nException: "
                       "(None, 's3_config.yaml')",
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'short_message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'watchman_name': 'Rorschach',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_config_load_failure_subject"),
            'success': False,
            'target': 'Generic S3 atg'
        }
        self.example_config_file = {
            "Daily": {
                '00': [
                    {
                        "target_name": "target1",
                        "items": [
                            {
                                "bucket_name": "bucket",
                                "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                                "suffix": ".parquet",
                                "min_total_size_kb": 50
                            },
                            {
                                "bucket_name": "bucket",
                                "prefix": "random/path/year=%0Y/month=%0m/day=%0d/",
                                "suffix": ".json",
                            }
                        ]
                    }
                ]
            }
        }
        self.example_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 22, 29)
        }, {
            'Key': 'some/path/to/something.json',
            'Size': 0,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 23, 29)
        }]
        self.example_generic_results = {
            "failures_and_exceptions": {
                'details': MESSAGES.get("failure_exception_message"),
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': MESSAGES.get("failure_exception_message"),
                'snapshot': {},
                'state': Watchman.STATE.get("failure"),
                'subject': MESSAGES.get("generic_failure_exception_subject"),
                'success': False,
                'target': 'Generic S3 atg',
                'watchman_name': 'Rorschach',
            },
            "failures": {
                'details': MESSAGES.get("failure_message"),
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': MESSAGES.get("failure_message"),
                'snapshot': {},
                'state': Watchman.STATE.get("failure"),
                'subject': MESSAGES.get("generic_failure_subject"),
                'success': False,
                'target': 'Generic S3 atg',
                'watchman_name': 'Rorschach',
            },
            "exceptions": {
                'details': MESSAGES.get("exception_message"),
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': MESSAGES.get("exception_message"),
                'snapshot': {},
                'state': Watchman.STATE.get("exception"),
                'subject': MESSAGES.get("generic_exception_subject"),
                'success': False,
                'target': 'Generic S3 atg',
                'watchman_name': 'Rorschach',
            },
            "success": {
                'details': MESSAGES.get("success_message"),
                'disable_notifier': True,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': MESSAGES.get("success_message"),
                'snapshot': {},
                'state': Watchman.STATE.get("success"),
                'subject': MESSAGES.get("generic_success_subject"),
                'success': True,
                'target': 'Generic S3 atg',
                'watchman_name': 'Rorschach',
            },
        }
        self.expected_invalid_event_email_result = {
            'details': MESSAGES.get("exception_invalid_event_details"),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'result_id': 0,
            'short_message': MESSAGES.get('exception_message'),
            'snapshot': {},
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_invalid_event_subject"),
            'success': False,
            'target': 'Generic S3 atg',
            'watchman_name': 'Rorschach',
        }
        self.process_checking_examples = [
            {
                "target_name": "target 1",
                "items": [
                    {
                        "bucket_name": "bad_bucket_example"
                    }
                ],
                "mocks": {
                    "mock_bucket": (False, None)
                },
                "processed_targets": {
                    "target 1": {
                        "success": False,
                        "exception_strings": [],
                        "failure_strings": [MESSAGES.get('failure_bucket_not_found').format("bad_bucket_example")]
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": False,
                        "short_message": MESSAGES.get("failure_message"),
                        "state": Watchman.STATE.get("failure"),
                        "subject": MESSAGES.get("failure_subject").format("target 1"),
                        "success": False,
                        "target": "target 1"
                    }
                ]
            },
            {
                "target_name": "target 2",
                "items": [
                    {
                        "bucket_name": "full_path_example",
                        "full_path": "path/to/file.json"
                    }
                ],
                "mocks": {
                    "mock_single_file_check": (["Exception 1"], ["Failure 1"])
                },
                "processed_targets": {
                    "target 2": {
                        "success": False,
                        "exception_strings": ["Exception 1"],
                        "failure_strings": ["Failure 1"]
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": False,
                        "short_message": MESSAGES.get("failure_exception_message"),
                        "state": Watchman.STATE.get("failure"),
                        "subject": MESSAGES.get("failure_exception_subject").format("target 2"),
                        "success": False,
                        "target": "target 2"
                    }
                ]
            },
            {
                "target_name": "target 3",
                "items": [
                    {
                        "bucket_name": "multiple_files_example"
                    }
                ],
                "mocks": {
                    "mock_multiple_files_check": (["Exception 2"], [])
                },
                "processed_targets": {
                    "target 3": {
                        "success": None,
                        "exception_strings": ["Exception 2"],
                        "failure_strings": []
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": False,
                        "short_message": MESSAGES.get("exception_message"),
                        "state": Watchman.STATE.get("exception"),
                        "subject": MESSAGES.get("exception_subject").format("target 3"),
                        "success": False,
                        "target": "target 3"
                    }
                ]
            },
            {
                "target_name": "target 4",
                "items": [
                    {
                        "bucket_name": "success_example",
                        "full_path": "path/to/file.json"
                    }
                ],
                "mocks": {},
                "processed_targets": {
                    "target 4": {
                        "success": True,
                        "exception_strings": [],
                        "failure_strings": []
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": True,
                        "short_message": MESSAGES.get("success_message"),
                        "state": Watchman.STATE.get("success"),
                        "subject": MESSAGES.get("success_subject").format("target 4"),
                        "success": True,
                        "target": "target 4"
                    }
                ]
            },
            {
                "target_name": "target 5",
                "items": [
                    {
                        "bucket_name": "success_example",
                        "full_path": "path/{var}/file.json",
                        "path_vars": ["to"]
                    }
                ],
                "mocks": {"mock_check_multiple_file_paths": ([], [])},
                "processed_targets": {
                    "target 5": {
                        "success": True,
                        "exception_strings": [],
                        "failure_strings": []
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": True,
                        "short_message": MESSAGES.get("success_message"),
                        "state": Watchman.STATE.get("success"),
                        "subject": MESSAGES.get("success_subject").format("target 5"),
                        "success": True,
                        "target": "target 5"
                    }
                ]
            },
            {
                "target_name": "target 6",
                "items": [
                    {
                        "bucket_name": "success_example",
                        "prefix": "path/{var}/",
                        "path_var": ["to"]
                    }
                ],
                "mocks": {"mock_check_multiple_file_paths": ([], [])},
                "processed_targets": {
                    "target 6": {
                        "success": True,
                        "exception_strings": [],
                        "failure_strings": []
                    }
                },
                "summary_parameters": [
                    {
                        "details": "Example details.",
                        "disable_notifier": True,
                        "short_message": MESSAGES.get("success_message"),
                        "state": Watchman.STATE.get("success"),
                        "subject": MESSAGES.get("success_subject").format("target 6"),
                        "success": True,
                        "target": "target 6"
                    }
                ]
            },

        ]
        self.example_s3_prefix = "s3://example/test.json"
        self.example_state_cases = {
            'E': [{
                'details': 'some details',
                'disable_notifier': False,
                'short_message': 'some message',
                'state': Watchman.STATE.get("exception"),
                'subject': 'Rorschach Exception',
                'success': None,
                'target': 'target 1',
            }, {
                'details': 'some details',
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': 'some message',
                'snapshot': {},
                'state': 'EXCEPTION',
                'subject': 'Rorschach Exception',
                'success': None,
                'target': 'target 1',
                'watchman_name': 'Rorschach',
            }],
            'F': [{
                'details': 'some details',
                'disable_notifier': False,
                'short_message': 'some message',
                'state': Watchman.STATE.get("failure"),
                'subject': 'Rorschach Failure',
                'success': False,
                'target': 'target 1',
            }, {
                'details': 'some details',
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': 'some message',
                'snapshot': {},
                'state': 'FAILURE',
                'subject': 'Rorschach Failure',
                'success': False,
                'target': 'target 1',
                'watchman_name': 'Rorschach',
            }],
            'T': [{
                'details': 'some details',
                'disable_notifier': True,
                'short_message': 'some message',
                'state': Watchman.STATE.get("success"),
                'subject': 'Rorschach Success',
                'success': True,
                'target': 'target 1',
            }, {
                'details': 'some details',
                'disable_notifier': True,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'result_id': 0,
                'short_message': 'some message',
                'snapshot': {},
                'state': 'SUCCESS',
                'subject': 'Rorschach Success',
                'success': True,
                'target': 'target 1',
                'watchman_name': 'Rorschach',
            }]
        }
        self.example_traceback = 'Traceback'
        # Variables dependent on pre-defined variables:
        self.example_create_results = {
            'TT': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('T')[1],
                   self.example_generic_results.get("success")
                   ],
            'TF': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('F')[1],
                   self.example_generic_results.get("failures")
                   ],
            'TE': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('E')[1],
                   self.example_generic_results.get("exceptions")
                   ],
            'FE': [self.example_state_cases.get('F')[1],
                   self.example_state_cases.get('E')[1],
                   self.example_generic_results.get("failures_and_exceptions")
                   ]
        }
        self.expected_invalid_config_file_result = {
            'details': MESSAGES.get("exception_config_load_failure_details").format(CONFIG_NAME,
                                                                                    self.example_traceback),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'short_message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'watchman_name': 'Rorschach',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_config_load_failure_subject"),
            'success': False,
            'target': 'Generic S3 atg'
        }

    def _create_rorschach(self):
        """
        Create a Rorschach object with a Daily event.
        @return: <Rorschach> rorschach object
        """
        return Rorschach(context=None, event=self.example_event_daily)

    def test_check_file_suffix(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_file_suffix
        """
        same_suffix_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)
        }]

        different_suffix_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)
        }, {
            'Key': 'some/path/to/something.json',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)
        }]

        suffix = '.parquet'
        rorschach_obj = self._create_rorschach()

        # Test for all correct suffixes:
        expected, expected_tb = "", None
        returned, returned_tb = rorschach_obj._check_file_suffix(same_suffix_contents, suffix)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test for failed suffix check:
        expected, expected_tb = "{}{}".format(different_suffix_contents[1].get('Key'), const.LINE_SEPARATOR), None
        returned, returned_tb = rorschach_obj._check_file_suffix(different_suffix_contents, suffix)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test for exceptions:
        expected, expected_tb = None, self.example_traceback
        returned, returned_tb = rorschach_obj._check_file_suffix(None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

    def test_check_invalid_event(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_invalid_event
        """
        tests = [
            {'event': 'monthly', 'expected': True},
            {'event': "weekly", 'expected': True},
            {'event': "daily", 'expected': True},
            {'event': "hourly", 'expected': True},
            {'event': "minutely", 'expected': True},
            {'event': "", 'expected': True},
            {'event': "Monthly", 'expected': False},
            {'event': "Weekly", 'expected': False},
            {'event': "Daily", 'expected': False},
            {'event': "Hourly", 'expected': False},
            {'event': "Minutely", 'expected': False}
        ]

        rorschach_obj = self._create_rorschach()
        for test in tests:
            rorschach_obj.event = test.get('event')
            returned = rorschach_obj._check_invalid_event()
            expected = test.get('expected')
            self.assertEqual(expected, returned)

    @patch('watchmen.process.rorschach.Rorschach._generate_contents')
    @patch('watchmen.process.rorschach.Rorschach._check_file_suffix')
    @patch('watchmen.process.rorschach.Rorschach._check_multiple_files_size')
    def test_check_multiple_files(self, mock_multiple_files_size_check, mock_suffix_check, mock_generate_contents):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_multiple_files_size
        """
        rorschach_obj = self._create_rorschach()
        example_contents_dicts = {
            "generate_contents_success": {
                "contents": self.example_contents,
                "count": 5,
                "s3_prefix": self.example_s3_prefix
            },
            "no_files_failure": {
                "contents": {},
                "count": 0,
                "s3_prefix": self.example_s3_prefix
            },
        }
        example_suffix_item = {
            "prefix": "example/path/",
            "time_offset": 2,
            "suffix": ".parquet",
        }
        example_total_files_item = {
            "prefix": "example/path/",
            "min_total_files": 10
        }

        # Test generate contents exception:
        mock_generate_contents.return_value = None, self.example_traceback

        expected_exception_strings = [MESSAGES.get("exception_string_format").format(example_suffix_item,
                                                                                     self.example_traceback)]
        expected_failure_strings = []

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(example_suffix_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test zero files failure:
        mock_generate_contents.return_value = example_contents_dicts.get("no_files_failure"), None

        expected_exception_strings = []
        expected_failure_strings = [MESSAGES.get('failure_no_files').format(self.example_s3_prefix)]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(example_suffix_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test suffix failure:
        bad_suffix_files = "bad_file1.json, bad_file2.json"
        mock_generate_contents.return_value = example_contents_dicts.get("generate_contents_success"), None
        mock_suffix_check.return_value = bad_suffix_files, self.example_traceback
        mock_multiple_files_size_check.return_value = None, None

        expected_exception_strings = ['Item: {}\n'. format(example_suffix_item) +
                                      'Exception: ' + self.example_traceback]
        expected_failure_strings = [MESSAGES.get('failure_invalid_suffix').format(example_suffix_item.get('suffix'),
                                                                                  bad_suffix_files)]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(example_suffix_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test check multiple files failure:
        mock_generate_contents.return_value = example_contents_dicts.get("generate_contents_success"), None
        mock_suffix_check.return_value = None, None
        mock_multiple_files_size_check.return_value = "File size failure check occurred.", self.example_traceback

        expected_exception_strings = ['Item: {}\n'. format(example_suffix_item) +
                                      'Exception: ' + self.example_traceback]
        expected_failure_strings = ["File size failure check occurred."]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(example_suffix_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test min total files failure:
        mock_generate_contents.return_value = example_contents_dicts.get("generate_contents_success"), None
        mock_suffix_check.return_value = None, None
        mock_multiple_files_size_check.return_value = None, None

        expected_exception_strings = []
        expected_failure_strings = [MESSAGES.get('failure_total_objects').format(
            self.example_s3_prefix, 5, example_total_files_item['min_total_files'])]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(
            example_total_files_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Testing success:
        mock_generate_contents.return_value = example_contents_dicts.get("generate_contents_success"), None
        mock_suffix_check.return_value = None, None
        mock_multiple_files_size_check.return_value = None, None

        expected_exception_strings = []
        expected_failure_strings = []

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_multiple_files(example_suffix_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

    def test_check_multiple_files_size(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_multiple_files_size
        """
        rorschach_obj = self._create_rorschach()
        example_successful_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 22, 29)
        }]

        examples = [
            {
                "contents": self.example_contents,
                "item": self.example_config_file['Daily']['00'][0].get('items')[0],
                "expected": "{}\n\n".format(MESSAGES.get('failure_file_empty').format(
                    self.example_contents[3]['Key'])) + MESSAGES.get('failure_multiple_file_size').format(
                    self.example_s3_prefix, 0.3, 50),
                "expected_tb": None
            },
            {
                "contents": example_successful_contents,
                "item": self.example_config_file['Daily']['00'][0].get('items')[1],
                "expected": "",
                "expected_tb": None
            }
        ]

        for example in examples:
            expected = example.get("expected")
            expected_tb = example.get("expected_tb")

            returned, returned_tb = rorschach_obj._check_multiple_files_size(example.get("contents"),
                                                                             example.get("item"),
                                                                             self.example_s3_prefix)
            self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Testing exception while checking multiple files size:
        expected, expected_tb = None, self.example_traceback

        returned, returned_tb = rorschach_obj._check_multiple_files_size(None, None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

    @patch('watchmen.process.rorschach.Rorschach._check_multiple_files')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file')
    def test_check_multiple_file_paths(self, mock_single_file, mock_multiple_files):
        rorschach_obj = self._create_rorschach()
        example_full_path = {
            "full_path": "example/bad/{var}/test.json",
            "path_vars": ["path"]
        }
        example_prefix = {
            "prefix": "example/bad/{var}/",
            "path_vars": ["path"]
        }
        tests = [
            {
                "item": example_full_path,
                "path_tag": "full_path",
                "file_return": (['oof'], ['exceptions']),
                "expected": (['oof'], ['exceptions'])
            },
            {
                "item": example_prefix,
                "path_tag": "prefix",
                "file_return": ([], []),
                "expected": ([], [])

            },
            {
                "item": {},
                "path_tag": "prefix",
                "file_return": ([], []),
                "expected": (['Item: {}\nException: Invalid path tag'], [])
            }
        ]
        for test in tests:
            mock_single_file.return_value = test.get('file_return')
            mock_multiple_files.return_value = test.get('file_return')
            expected = test.get('expected')
            result = rorschach_obj._check_multiple_file_paths(test.get('item'))
            self.assertEqual(expected, result)

    @patch('watchmen.process.rorschach.Rorschach._generate_key')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file_existence')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file_size')
    @patch('watchmen.process.rorschach.Rorschach._trim_contents')
    def test_check_single_file(self, mock_trim_contents, mock_check_size, mock_check_existence, mock_generate_key):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_single_file
        """
        rorschach_obj = self._create_rorschach()
        example_item = {
            "full_path": "example/bad/path/test.json",
            "time_offset": 2,
            "min_total_size_kb": 50,
            "bucket_name": "example_bucket"
        }

        # Test for generate_key failure:
        mock_trim_contents.return_value = [{}]
        mock_generate_key.return_value = None, self.example_traceback

        expected_exception_string = self.example_traceback
        expected_failure_strings = []

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(example_item)
        self.assertEqual(expected_failure_strings, returned_failure_strings)
        self.assertTrue(expected_exception_string in returned_exception_strings[0])

        # Test for single file existence check failure:
        mock_generate_key.return_value = self.example_s3_prefix, None
        mock_check_existence.return_value = False, None

        expected_exception_strings = []
        expected_failure_strings = [MESSAGES.get('failure_invalid_s3_key').format(self.example_s3_prefix)]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(example_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test for single file existence check exception:
        mock_generate_key.return_value = self.example_s3_prefix, None
        mock_check_existence.return_value = False, self.example_traceback

        expected_exception_strings = ['Item: {}\n'. format(example_item) + 'Exception: ' + self.example_traceback]
        expected_failure_strings = []

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(example_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test for single file size check failure:
        mock_generate_key.return_value = self.example_s3_prefix, None
        mock_check_existence.return_value = True, None
        mock_check_size.return_value = False, self.example_traceback

        expected_exception_strings = ['Item: {}\n'. format(example_item) + 'Exception: ' + self.example_traceback]
        expected_failure_strings = [MESSAGES.get('failure_single_file_size').format(
            example_item.get("min_total_size_kb"), self.example_s3_prefix)]

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(example_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # Test for success:
        mock_generate_key.return_value = self.example_s3_prefix, None
        mock_check_existence.return_value = True, None
        mock_check_size.return_value = True, None

        expected_exception_strings = []
        expected_failure_strings = []

        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(example_item)
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

        # test for Trim contents failure
        trimmable_item = {
            "full_path": "example/bad/path/test.json",
            "time_offset": 2,
            "min_total_size_kb": 50,
            "bucket_name": "example_bucket",
            "offset_type": "Hourly"
        }
        time_now = datetime.datetime.now(pytz.utc).replace(second=0, microsecond=0)
        date_range = "{} to {}".format(time_now.strftime('%m-%d-%y'), time_now.strftime('%m-%d-%y'))
        mock_trim_contents.return_value = None
        returned_exception_strings, returned_failure_strings = rorschach_obj._check_single_file(trimmable_item)
        expected_exception_strings = []
        expected_failure_strings = [MESSAGES.get('failure_last_modified_date').
                                    format(self.example_s3_prefix, date_range)]
        self.assertEqual((expected_exception_strings, expected_failure_strings),
                         (returned_exception_strings, returned_failure_strings))

    @patch('watchmen.process.rorschach._s3.validate_file_on_s3')
    def test_check_single_file_existence(self, mock_valid):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_single_file_existence
        """
        rorschach_obj = self._create_rorschach()
        s3_key_example = 'some/path/to/something.parquet'
        item = {
            "bucket_name": "bucket",
            "full_path": "some/path/to/something.parquet"
        }

        # Testing successful file existence check:
        mock_valid.return_value = True
        expected, expected_tb = True, None
        returned, returned_tb = rorschach_obj._check_single_file_existence(item, s3_key_example)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Testing exception while checking single file existence:
        mock_valid.side_effect = Exception
        returned, returned_tb = rorschach_obj._check_single_file_existence(item, s3_key_example)
        self.assertEqual(None, returned)
        self.assertTrue(self.example_traceback in returned_tb)

    @patch('botocore.client.BaseClient._make_api_call')
    def test_check_single_file_size(self, mock_get_object):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_single_file_size
        """
        rorschach_obj = self._create_rorschach()
        example_item = {
            "bucket_name": "random-bucket-that-doesnt-exist",
            "min_total_size_kb": 1
        }

        # Test file size check success:
        mock_get_object.return_value = {"ContentLength": 10000}
        expected, expected_tb = True, None
        returned, returned_tb = rorschach_obj._check_single_file_size(example_item, "random-s3-key/example.json")
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test file size check failure:
        mock_get_object.return_value = {"ContentLength": 100}
        expected, expected_tb = False, None
        returned, returned_tb = rorschach_obj._check_single_file_size(example_item, "random-s3-key/example.json")
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test file size check exception:
        mock_get_object.return_value = {}
        expected, expected_tb = None, self.example_traceback
        returned, returned_tb = rorschach_obj._check_single_file_size(example_item, "random-s3-key/example.json")
        self.assertEqual(expected, returned)
        self.assertTrue(self.example_traceback in returned_tb)

    def test_create_config_not_load_result(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_config_not_load_result
        """
        rorschach_obj = self._create_rorschach()
        returned = rorschach_obj._create_config_not_load_result(self.example_traceback)
        returned = returned[0].to_dict()
        returned["dt_created"] = "2020-12-15T00:00:00+00:00"
        self.assertEqual(self.expected_invalid_config_file_result, returned)

    def test_create_details(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_details
        """
        rorschach_obj = self._create_rorschach()
        example_exception_strings = ["Exception 1", "Exception 2"]
        example_failure_strings = ["Failure 1", "Failure 2"]
        example_target_check_results = {
            "success_target": {
                "success": True,
                "exception_strings": [],
                "failure_strings": [],
                "expected_details": MESSAGES.get("success_details").format("success_target")
            },
            "exception_target": {
                "success": None,
                "exception_strings": example_exception_strings,
                "failure_strings": [],
                "expected_details": MESSAGES.get('exception_details').format("\n\n".join(example_exception_strings))
            },
            "failure_target": {
                "success": False,
                "exception_strings": example_exception_strings,
                "failure_strings": example_failure_strings,
                "expected_details":
                    MESSAGES.get("failure_details").format("\n\n".join(example_failure_strings)) + "\n\n{}\n\n{}".
                    format(const.MESSAGE_SEPARATOR, MESSAGES.get('exception_details').format(
                        "\n\n".join(example_exception_strings)))
            }
        }

        for target_name in example_target_check_results:
            expected_details = example_target_check_results.get(target_name).get("expected_details")
            returned_details = rorschach_obj._create_details(target_name, example_target_check_results.get(target_name))
            self.assertEqual(expected_details, returned_details)

    def test_create_generic_result(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_generic_result
        """
        rorschach_obj = self._create_rorschach()

        example_parameters = {
            "failures_and_exceptions": {
                'failure_in_parameters': True,
                'exception_in_parameters': True,
                'details': MESSAGES.get("failure_exception_message")
            },
            "failures": {
                'failure_in_parameters': True,
                'exception_in_parameters': False,
                'details': MESSAGES.get("failure_message")
            },
            "exceptions": {
                'failure_in_parameters': False,
                'exception_in_parameters': True,
                'details': MESSAGES.get("exception_message")
            },
            "success": {
                'failure_in_parameters': False,
                'exception_in_parameters': False,
                'details': MESSAGES.get("success_message")
            },
        }

        for parameters in example_parameters:
            expected = self.example_generic_results.get(parameters)
            returned = rorschach_obj._create_generic_result(example_parameters[parameters]['failure_in_parameters'],
                                                            example_parameters[parameters]['exception_in_parameters'],
                                                            example_parameters[parameters]['details'])
            returned = returned.to_dict()
            returned['dt_created'] = '2020-12-15T00:00:00+00:00'
            self.assertEqual(expected, returned)

    def test_create_invalid_event_result(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_invalid_event_result
        """
        rorschach_obj = self._create_rorschach()
        returned = rorschach_obj._create_invalid_event_result()
        returned = returned[0].to_dict()
        returned["dt_created"] = "2020-12-15T00:00:00+00:00"
        self.assertEqual(self.expected_invalid_event_email_result, returned)

    @patch('watchmen.process.rorschach.Rorschach._create_generic_result')
    def test_create_results(self, mock_generic_result):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_result
        """
        rorschach_obj = self._create_rorschach()
        mock_generic_results = {
            "TT": self.example_generic_results.get("success"),
            "TF": self.example_generic_results.get("failures"),
            "TE": self.example_generic_results.get("exceptions"),
            "FE": self.example_generic_results.get("failures_and_exceptions")
        }
        example_state_cases_summary = {
            'TT': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('T')[0]
                   ],
            'TF': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('F')[0]
                   ],
            'TE': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('E')[0]
                   ],
            'FE': [self.example_state_cases.get('F')[0],
                   self.example_state_cases.get('E')[0]
                   ]
        }

        for key in self.example_create_results:
            summary = example_state_cases_summary.get(key)
            expected_result_list = self.example_create_results.get(key)
            mock_generic_result.return_value = mock_generic_results.get(key)

            result = rorschach_obj._create_results(summary)
            returned = []
            # The mocked generic result is already a dict, so it doesn't need to be converted:
            for obj in result[:2]:
                obj = obj.to_dict()
                obj['dt_created'] = '2020-12-15T00:00:00+00:00'
                returned.append(obj)
            # Append the mocked generic result:
            returned.append(result[2])
            self.assertEqual(expected_result_list, returned)

    @patch('watchmen.process.rorschach.Rorschach._create_details')
    def test_create_summary_parameters(self, mock_details):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_summary_parameters
        """
        rorschach_obj = self._create_rorschach()
        mock_details.return_value = "Example details."

        for target_example in self.process_checking_examples:
            processed_target_example = target_example.get("processed_targets")
            expected = target_example.get("summary_parameters")
            returned = rorschach_obj._create_summary_parameters(processed_target_example)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.rorschach.Rorschach._generate_prefixes')
    @patch('watchmen.process.rorschach._s3.generate_pages')
    @patch('watchmen.process.rorschach.Rorschach._remove_whitelisted_files_from_contents')
    def test_generate_contents(self, mock_whitelist, mock_pages, mock_prefixes):
        """
        test watchmen.process.rorschach :: Rorschach :: _generate_contents
        """
        rorschach_obj = self._create_rorschach()
        item = self.example_config_file['Daily']['00'][0].get('items')[0]

        # Test successful _generate_contents call
        mock_prefixes.return_value = ['some/path/to/'], None
        mock_pages.return_value = self.example_contents

        expected_dict = {
            "contents": self.example_contents,
            "count": len(self.example_contents),
            "s3_prefix": 's3://bucket/some/path/to/'
        }
        expected_tb = None

        returned_dict, returned_tb = rorschach_obj._generate_contents(item)
        self.assertEqual((expected_dict, expected_tb), (returned_dict, returned_tb))

        # Testing exception:
        expected_dict = {
            "contents": None,
            "count": None,
            "s3_prefix": None
        }

        returned_dict, returned_tb = rorschach_obj._generate_contents(None)
        self.assertEqual(returned_dict, expected_dict)
        self.assertTrue(self.example_traceback in returned_tb)

        # Testing exception:
        expected_dict = {
            "contents": None,
            "count": None,
            "s3_prefix": None
        }

        mock_prefixes.return_value = None, self.example_traceback
        returned_dict, returned_tb = rorschach_obj._generate_contents(item)
        self.assertEqual(returned_dict, expected_dict)

        # Test Max Items
        max_item = {
                "bucket_name": "bucket",
                "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                "suffix": ".parquet",
                "min_total_size_kb": 50,
                'max_items': 0,
                'offset_type': 'Daily'
               }

        expected = {'contents': [], 'count': 0, 's3_prefix': 's3://bucket/some/path/to/'}
        mock_prefixes.return_value = ['some/path/to/'], None
        mock_pages.return_value = {}
        returned_dict, returned_tb = rorschach_obj._generate_contents(max_item)
        self.assertEqual(returned_dict, expected)

        # Test trim contents
        max_item = {
                "bucket_name": "bucket",
                "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                "suffix": ".parquet",
                "min_total_size_kb": 50,
                'max_items': 1,
                'offset_type': 'Hourly'
               }

        expected = {'contents': [], 'count': 0, 's3_prefix': 's3://bucket/some/path/to/'}
        mock_prefixes.return_value = ['some/path/to/'], None
        mock_pages.return_value = {}
        returned_dict, returned_tb = rorschach_obj._generate_contents(max_item)
        self.assertEqual(returned_dict, expected)

        # Test whitelist
        max_item = {
                "bucket_name": "bucket",
                "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                "suffix": ".parquet",
                "min_total_size_kb": 50,
                'max_items': 1,
                'whitelist': 'test'
               }

        expected = {'contents': [], 'count': 0, 's3_prefix': 's3://bucket/some/path/to/'}
        mock_prefixes.return_value = ['some/path/to/'], None
        mock_pages.return_value = {}
        returned_dict, returned_tb = rorschach_obj._generate_contents(max_item)
        self.assertEqual(returned_dict, expected)

    def test_generate_key(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _generate_key
        """
        prefix_format_example = 'some/path/year=%0Y/month=%0m/day=%0d/'
        check_time_example = datetime.datetime.now(pytz.utc) - datetime.timedelta(**{'days': 1})
        rorschach_obj = self._create_rorschach()

        # Test successful key generation with default time_offset:
        expected, expected_tb = check_time_example.strftime(prefix_format_example), None
        event_frequency = list(self.example_event_daily.get('Type').keys())[0]
        returned, returned_tb = rorschach_obj._generate_key(prefix_format_example, event_frequency)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test successful key generation with specified time_offset:
        check_time_example = datetime.datetime.now(pytz.utc) - datetime.timedelta(**{'days': 3})
        expected, expected_tb = check_time_example.strftime(prefix_format_example), None
        event_frequency = list(self.example_event_daily.get('Type').keys())[0]
        returned, returned_tb = rorschach_obj._generate_key(prefix_format_example,
                                                            event_frequency, 3)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test successful key generation with month time_offset:
        check_time_example = datetime.datetime.now(pytz.utc) - relativedelta(**{'months': 1})
        expected, expected_tb = check_time_example.strftime(prefix_format_example), None
        returned, returned_tb = rorschach_obj._generate_key(prefix_format_example, "Monthly")
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # Test exception while generating key:
        expected, expected_tb = None, 'Traceback'
        returned, returned_tb = rorschach_obj._generate_key(None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

    def test_generate_prefixes(self):
        prefix_format_example = 'some/path/year=%0Y/month=%0m/day=%0d/'
        now = datetime.datetime.now(pytz.utc)
        check_time_example = now - datetime.timedelta(**{'days': 1})
        rorschach_obj = self._create_rorschach()

        # Test multiple prefixes (one for each day) when using daily offset
        expected = [now.strftime(prefix_format_example), check_time_example.strftime(prefix_format_example)]
        expected_tb = None
        event_frequency = list(self.example_event_daily.get('Type').keys())[0]
        returned, returned_tb = rorschach_obj._generate_prefixes(prefix_format_example, event_frequency)
        self.assertEqual((set(expected), expected_tb), (set(returned), returned_tb))

        # Test exception while generating key:
        expected, expected_tb = None, 'Traceback'
        returned, returned_tb = rorschach_obj._generate_key(None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

        # Test exception while generating key:
        expected, expected_tb = None, 'Traceback'
        returned, returned_tb = rorschach_obj._generate_prefixes(None, None)
        self.assertEqual(expected, returned)

    @patch('builtins.open', new_callable=mock_open())
    @patch('watchmen.process.rorschach.yaml.load')
    def test_load_config(self, mock_file, mock_open):
        """
        test watchmen.process.rorschach :: Rorschach :: _load_config
        """

        with mock_open:
            rorschach_obj = self._create_rorschach()

            # Testing successful load of config file:
            mock_file.return_value = self.example_config_file
            expected = self.example_config_file['Daily']['00']
            returned, returned_tb = rorschach_obj._load_config(['Daily', '00'])
            self.assertEqual((expected, None), (returned, returned_tb))

            # Testing exception while loading config file:
            mock_file.return_value = None
            mock_open.side_effect = Exception
            returned, returned_msg = rorschach_obj._load_config('')
            self.assertEqual(None, returned)
            self.assertTrue(Exception, returned_msg)

    @patch('watchmen.process.rorschach.Rorschach._check_invalid_event')
    @patch('watchmen.process.rorschach.Rorschach._load_config')
    @patch('watchmen.process.rorschach.Rorschach._process_checking')
    @patch('watchmen.process.rorschach.Rorschach._create_summary_parameters')
    @patch('watchmen.process.rorschach.Rorschach._create_results')
    def test_monitor(self, mock_result, mock_summary, mock_checking, mock_config, mock_event):
        """
        test watchmen.process.rorschach :: Rorschach :: monitor
        """
        rorschach_obj = self._create_rorschach()
        example_process_checking_result = {
            "target1": {
                "success": True,
                "exception_strings": [],
                "failure_strings": []
            }
        }

        # check a success case
        mock_event.return_value = False
        mock_config.return_value = self.example_config_file.get('Daily'), None
        mock_checking.return_value = example_process_checking_result
        mock_summary.return_value = [{
            "details": MESSAGES.get("success_details").format("target1"),
            "disable_notifier": True,
            "short_message": MESSAGES.get("success_message"),
            "state": Watchman.STATE.get("success"),
            "subject": MESSAGES.get("success_subject").format("target1"),
            "success": True,
            "target": "target1"
        }]
        mock_result.return_value = self.example_create_results.get('TT')
        expected = mock_result()
        returned = rorschach_obj.monitor()
        self.assertEqual(expected, returned)

        # check a case with invalid event
        mock_event.return_value = True
        returned = rorschach_obj.monitor()
        returned = returned[0].to_dict()
        returned['dt_created'] = '2020-12-15T00:00:00+00:00'
        self.assertEqual(returned, self.expected_invalid_event_email_result)

        # check a case with s3 target file not loaded
        mock_event.return_value = False
        mock_config.return_value = None, self.example_traceback
        returned = rorschach_obj.monitor()
        returned = returned[0].to_dict()
        returned['dt_created'] = '2020-12-15T00:00:00+00:00'
        self.assertEqual(returned, self.expected_invalid_config_file_result)

    @patch('watchmen.process.rorschach.traceback.format_exc')
    def test_parse_event(self, mock_tb):
        """
        test watchmen.process.rorschach :: Rorschach :: _get_config_path
        """

        tests = [
            {
                'event': self.example_event_daily,
                'expected': ('Daily', ['Daily', '15:00'], None),
                'tb': None
            },
            {
                'event': self.example_event_weekly,
                'expected': ('Weekly', ['Weekly', 'Mon', '10:45'], None),
                'tb': None
            },
            {
                'event': {'Type': ''},
                'expected': (None, None, self.example_traceback),
                'tb': self.example_traceback
            }
        ]

        for test in tests:
            mock_tb.return_value = test.get('tb')
            event = test.get("event")
            expected = test.get("expected")
            test_rorschach = Rorschach(context=None, event=event)
            result = test_rorschach._parse_event()
            self.assertEqual(expected, result)

    @patch('watchmen.process.rorschach._s3.check_bucket')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file')
    @patch('watchmen.process.rorschach.Rorschach._check_multiple_files')
    def test_process_checking(self, mock_multiple_files_check, mock_single_file_check, mock_bucket_check):
        """
        test watchmen.process.rorschach :: Rorschach :: _process_checking
        """
        rorschach_obj = self._create_rorschach()

        for target_example in self.process_checking_examples:
            mocks = target_example.get("mocks")
            mock_bucket_check.return_value = mocks.get("mock_bucket", (True, None))
            mock_single_file_check.return_value = mocks.get("mock_single_file_check", ([], []))
            mock_multiple_files_check.return_value = mocks.get("mock_multiple_files_check", ([], []))

            expected = target_example.get("processed_targets")
            returned = rorschach_obj._process_checking([target_example])
            self.assertEqual(expected, returned)

        # Check Bucket exception
        mocks = self.process_checking_examples[0].get("mocks")
        mock_bucket_check.return_value = (True, self.example_traceback)
        mock_single_file_check.return_value = mocks.get("mock_single_file_check", ([], []))
        mock_multiple_files_check.return_value = mocks.get("mock_multiple_files_check", ([], []))

        expected = {"target 1": {
                    "success": None,
                    "exception_strings": [MESSAGES.get("exception_string_format").format(
                        {'bucket_name': "bad_bucket_example"},
                        self.example_traceback)],
                    "failure_strings": []
                    }}
        returned = rorschach_obj._process_checking([self.process_checking_examples[0]])
        self.assertEqual(expected, returned)

    def test_remove_whitelisted_files_from_contents(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _remove_whitelisted_files_from_contents
        """
        rorschach_obj = self._create_rorschach()
        example_whitelist = ['something.json']
        expected_returned_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': datetime.datetime(2020, 5, 20, 0, 22, 29)
        }]

        returned = rorschach_obj._remove_whitelisted_files_from_contents(example_whitelist, self.example_contents)
        self.assertEqual(returned, expected_returned_contents)

    def test_trim_contents(self):

        example_return_hourly = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': (datetime.datetime.now(pytz.utc) -
                             datetime.timedelta(**{'hours': 0.5})).replace(second=0, microsecond=0)
        }]

        example_contents = [{
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': (datetime.datetime.now(pytz.utc) -
                             datetime.timedelta(**{'days': 3})).replace(second=0, microsecond=0)
        }, {
            'Key': 'some/path/to/something.parquet',
            'Size': 100,
            'LastModified': (datetime.datetime.now(pytz.utc) -
                             datetime.timedelta(**{'hours': 0.5})).replace(second=0, microsecond=0)
        }]

        rorschach_obj = self._create_rorschach()
        returned = rorschach_obj._trim_contents(example_contents, 1, "Hourly")
        returned[0]['LastModified'] = returned[0]['LastModified'].replace(second=0, microsecond=0)
        self.assertEqual(example_return_hourly, returned)
