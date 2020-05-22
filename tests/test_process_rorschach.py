import datetime
from mock import patch, mock_open, MagicMock, Mock
import pytz
import unittest

# from watchmen.common.result import Result
from watchmen.process.rorschach import Rorschach
from watchmen.process.rorschach import MESSAGES


class TestRorschach(unittest.TestCase):

    def setUp(self):
        self.example_event_daily = {'Type': 'Daily'}
        self.example_event_hourly = {'Type': 'Hourly'}
        self.example_invalid_events = [
            {'Type': 'hourly'},
            {'Type': 'daily'},
            {'type': 'Hourly'},
            {'type': 'Daily'},
            {'': ''},
            {}
        ]
        self.example_config_path = '../watchmen/process/s3_config.yaml'
        self.expected_invalid_event_email_result = {
            'details': MESSAGES.get("exception_invalid_event_details"),
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'dt_updated': '2020-12-15T00:00:00+00:00',
            'is_ack': False,
            'is_notified': False,
            'message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'source': 'Rorschach',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_invalid_event_subject"),
            'success': False,
            'target': 'Generic S3'
        }
        self.expected_invalid_config_file_result = {
            'details': "Cannot load S3 targets from file:\ns3_config.yaml\nException: (None, 's3_config.yaml')",
            'disable_notifier': False,
            'dt_created': '2020-12-15T00:00:00+00:00',
            'dt_updated': '2020-12-15T00:00:00+00:00',
            'is_ack': False,
            'is_notified': False,
            'message': MESSAGES.get('exception_message'),
            'result_id': 0,
            'snapshot': {},
            'source': 'Rorschach',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_config_not_load_subject"),
            'success': False,
            'target': 'Generic S3'
        }
        self.example_config_file = {
            "Daily": [
                {
                    "target_name": "target1",
                    "items": [
                        {
                            "bucket_name": "bucket",
                            "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                            "suffix": ".parquet"
                        }
                    ]
                },
                {
                    "target_name": "target1",
                    "items": [
                        {
                            "bucket_name": "bucket",
                            "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                            "suffix": ".parquet"
                        }
                    ]
                }
            ]}
        self.process_checking_result = {"target1": [], "target1": []}
        self.example_success_summary = {
            "success": True,
            "subject": MESSAGES.get("success_subject").format("target1"),
            "details": MESSAGES.get("success_details").format("target1"),
            "message": MESSAGES.get("success_message").format("target1"),
            "target": "target1"
        }
        self.create_summary_example = [self.example_success_summary,
                                       self.example_success_summary]
        self.example_summary_results = [{
            "success": True,
            "subject": MESSAGES.get("success_subject").format('target1'),
            "details": MESSAGES.get("success_details").format('target1'),
            "message": MESSAGES.get("success_message").format('target1'),
            "target": 'target1'
        },
            {
                "message": MESSAGES.get("failure_message").format('target2'),
                "success": False,
                "subject": MESSAGES.get("failure_subject").format('target2'),
                "details": 'There is at least one key of the data in S3 is not matched with '
                           'configuration.\n'
                           'This file: True is empty for target data in S3.\n'
                           'This file: '
                           "['some/path/to/something.parquet'] "
                           'is empty for target data in S3.\n'
                           'The size of all files founded in '
                           's3://bucket/some/path/to/ '
                           'is 0.2 KB, which is less than expected total file size 0.3 KB.\n'
                           'The number of objects founded in '
                           's3://bucket/some/path/to/ '
                           'is 2, which is less than expected total objects count 3.\n',
                "target": 'target2'
            },
            {'details': 'No file found here: some/path/to/something.zip.\n',
             'message': MESSAGES.get("failure_message").format('target3'),
             'subject': MESSAGES.get("failure_subject").format('target3'),
             'success': False,
             'target': 'target3'}

        ]
        self.example_process_ex_results = {'target1': ['some']}
        self.msg_process_ex_results = "An error occurred while checking the target at due to the following: " \
                                      "AttributeError: 'str' object has no attribute 'keys'"
        self.example_summary_ex_results = [{
            "message": MESSAGES.get("exception_message"),
            "success": None,
            "subject": MESSAGES.get("exception_subject"),
            "details": self.msg_process_ex_results,
            "target": 'target1'
        }]
        self.example_case = {
            'T': [{'success': True, 'subject': 'Rorschach Success', 'details': 'some details',
                   'message': 'some message', 'target': 'target 1'},
                  {'details': 'some details', 'disable_notifier': True, 'dt_created': '2020-12-15T00:00:00+00:00',
                   'dt_updated': '2020-12-15T00:00:00+00:00', 'is_ack': False, 'is_notified': False,
                   'message': 'some message', 'result_id': 0,
                   'snapshot': None, 'source': 'Rorschach', 'state': 'SUCCESS', 'subject': 'Rorschach Success',
                   'success': True, 'target': 'target 1'}],
            'F': [{'success': False, 'subject': 'Rorschach Failure', 'details': 'some details',
                   'message': 'some message', 'target': 'target 1'},
                  {'details': 'some details', 'disable_notifier': False, 'dt_created': '2020-12-15T00:00:00+00:00',
                   'dt_updated': '2020-12-15T00:00:00+00:00', 'is_ack': False, 'is_notified': False,
                   'message': 'some message', 'result_id': 0,
                   'snapshot': None, 'source': 'Rorschach', 'state': 'FAILURE', 'subject': 'Rorschach Failure',
                   'success': False, 'target': 'target 1'}],
            'E': [{'success': None, 'subject': 'Rorschach Exception',
                   'details': 'some details', 'message': 'some message', 'target': 'target 1'},
                  {'details': 'some details', 'disable_notifier': False, 'dt_created': '2020-12-15T00:00:00+00:00',
                   'dt_updated': '2020-12-15T00:00:00+00:00', 'is_ack': False, 'is_notified': False,
                   'message': 'some message', 'result_id': 0,
                   'snapshot': None, 'source': 'Rorschach', 'state': 'EXCEPTION', 'subject': 'Rorschach Exception',
                   'success': None, 'target': 'target 1'}]
        }
        self.expected_result = {
            'TT': [self.example_case.get('T')[0],
                   self.example_case.get('T')[0]],
            'TF': [self.example_case.get('T')[0],
                   self.example_case.get('F')[0]],
            'TE': [self.example_case.get('T')[0],
                   self.example_case.get('E')[0]],
            'EF': [self.example_case.get('F')[0],
                   self.example_case.get('E')[0]]
        }
        self.expected_return = {
            'TT': [self.example_case.get('T')[1],
                   self.example_case.get('T')[1],
                   {'details': 'Rorschach Success\nsome details\n\nRorschach Success\nsome details\n\n',
                    'disable_notifier': True, 'dt_created': '2020-12-15T00:00:00+00:00',
                    'dt_updated': '2020-12-15T00:00:00+00:00',
                    'is_ack': False, 'is_notified': False,
                    'message': MESSAGES.get("success_message").format('All targets'),
                    'result_id': 0, 'snapshot': None, 'source': 'Rorschach', 'state': 'SUCCESS',
                    'subject': MESSAGES.get("generic_suceess_subject"), 'success': True, 'target': 'Generic S3'}],
            'TF': [self.example_case.get('T')[1],
                   self.example_case.get('F')[1],
                   {'details': 'Rorschach Success\nsome details\n\nRorschach Failure\nsome details\n\n',
                    'disable_notifier': False, 'dt_created': '2020-12-15T00:00:00+00:00',
                    'dt_updated': '2020-12-15T00:00:00+00:00',
                    'is_ack': False,
                    'is_notified': False, 'message': MESSAGES.get("failure_message"), 'result_id': 0, 'snapshot': None,
                    'source': 'Rorschach',
                    'state': 'FAILURE', 'subject': MESSAGES.get("generic_failure_subject"), 'success': False,
                    'target': 'Generic S3'}],
            'TE': [self.example_case.get('T')[1],
                   self.example_case.get('E')[1],
                   {'details': 'Rorschach Success\nsome details\n\nRorschach Exception\nsome details\n\n',
                    'disable_notifier': False, 'dt_created': '2020-12-15T00:00:00+00:00',
                    'dt_updated': '2020-12-15T00:00:00+00:00',
                    'is_ack': False,
                    'is_notified': False, 'message': MESSAGES.get("exception_message"), 'result_id': 0,
                    'snapshot': None,
                    'source': 'Rorschach',
                    'state': 'EXCEPTION', 'subject': MESSAGES.get("generic_exception_subject"), 'success': None,
                    'target': 'Generic S3'}],
            'EF': [self.example_case.get('F')[1],
                   self.example_case.get('E')[1],
                   {'details': 'Rorschach Failure\nsome details\n\nRorschach Exception\nsome details\n\n',
                    'disable_notifier': False, 'dt_created': '2020-12-15T00:00:00+00:00',
                    'dt_updated': '2020-12-15T00:00:00+00:00',
                    'is_ack': False,
                    'is_notified': False,
                    'message': MESSAGES.get("exception_message") + MESSAGES.get("failure_message"),
                    'result_id': 0, 'snapshot': None, 'source': 'Rorschach',
                    'state': 'EXCEPTION', 'subject': MESSAGES.get("generic_fail_exception_subject"), 'success': None,
                    'target': 'Generic S3'}]}

        self.example_contents = [{'Key': 'some/path/to/something.parquet', 'Size': 100,
                                  'LastModified': datetime.datetime(2020, 5, 20, 0, 20, 29)},
                                 {'Key': 'some/path/to/something.parquet', 'Size': 100,
                                  'LastModified': datetime.datetime(2020, 5, 20, 0, 21, 29)},
                                 {'Key': 'some/path/to/something.parquet', 'Size': 100,
                                  'LastModified': datetime.datetime(2020, 5, 20, 0, 22, 29)},
                                 {'Key': 'some/path/to/something.json', 'Size': 0,
                                  'LastModified': datetime.datetime(2020, 5, 20, 0, 23, 29)}]

        # The key name need to be changed to edge case name, ex 'success', 'no_file_found_ex'
        self.result = {
            'target1': {
                "input": [{"target_name": 'target1',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "prefix": "some/path/to/",
                                   "suffix": ".parquet",
                                   "check_total_object": 1,
                                   "check_total_size_kb": 0,
                                   "check_most_recent_file": 2
                               }
                           ]}],
                "return": {
                    'target': 'target1',
                    'bucket_result': {'okay': True, 'err': None},
                    'contents': ([{'Size': 100, 'Key': 'some/path/to/something.parquet'},
                                  {'Size': 100, 'Key': 'some/path/to/something.parquet'},
                                  {'Size': 100, 'Key': 'some/path/to/something.parquet'}], 3,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'recent_contents': ([{'Size': 100, 'Key': 'some/path/to/something.parquet'},
                                         {'Size': 100, 'Key': 'some/path/to/something.parquet'}], 2),
                    'prefix_suffix': (True, None),
                    'file_empty': (False, [], None),
                    'file_size': (True, 0.2, None),
                    'expected_result': {'success': True, 'failed_checks': []}
                }},
            'target2': {
                "input": [{"target_name": 'target2',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "prefix": "some/path/to/",
                                   "suffix": ".parquet",
                                   "check_total_object": 5,
                                   "check_total_size_kb": 0.5
                               }
                           ]}],
                "return": {
                    'target': 'target2',
                    'bucket_result': {'okay': True, 'err': None},
                    'contents': ([{'Size': 100, 'Key': 'some/path/to/something.json'},
                                  {'Size': 100, 'Key': 'some/path/to/something.parquet'},
                                  {'Size': 0, 'Key': 'some/path/to/something.parquet'}], 3,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'prefix_suffix': (False, None),
                    'file_empty': (True, ['some/path/to/something.parquet'], None),
                    'file_size': (True, 0.2, None),
                    'expected_result': {'failed_checks': [({"bucket_name": "bucket",
                                                            "prefix": "some/path/to/",
                                                            "suffix": ".parquet",
                                                            "check_total_object": 5,
                                                            "check_total_size_kb": 0.5},
                                                           {'at_least_one_file_empty': (True,
                                                                                        [
                                                                                            'some/path/to/something.parquet']),
                                                            'count_object_too_less': ('s3://some/path/to/',
                                                                                      3,
                                                                                      5),
                                                            'prefix_suffix_not_match': ('some/path/to/',
                                                                                        '.parquet'),
                                                            'total_file_size_below_threshold': ('s3://some/path/to/',
                                                                                                0.2,
                                                                                                0.5)})],
                                        'success': False}}
            },
            'target3': {
                "input": [{"target_name": 'target3',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                               }
                           ]}],
                "return": {
                    'target': 'target3',
                    'bucket_result': {'okay': False, 'err': None},
                    'expected_result': {'failed_checks': [({'bucket_name': 'bucket'},
                                                           {'bucket_not_found': 's3://{}'.format('bucket')}
                                                           )], 'success': False}
                }},
            'target4': {
                "input": [{"target_name": 'target4',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                               }
                           ]}],
                "return": {
                    'target': 'target4',
                    'bucket_result': {'okay': None, 'err': Exception},
                    'expected_result': {'failed_checks': [({'bucket_name': 'bucket'},
                                                           {'exception': Exception}
                                                           )], 'success': None}
                }},
            'target5': {
                "input": [{"target_name": 'target5',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "full_path": "some/path/to/something.parquet"
                               }
                           ]}],
                "return": {
                    'target': 'target5',
                    'bucket_result': {'okay': True, 'err': None},
                    'full_path': (False, "s3://bucket/some/path/to/something.parquet", None),

                    'expected_result': {'success': False, 'failed_checks': [({
                                                                                 "bucket_name": "bucket",
                                                                                 "full_path": "some/path/to/something.parquet"
                                                                             }
                    , {'no_file_found': "s3://bucket/some/path/to/something.parquet"})]}
                }},
            'target6': {
                "input": [{"target_name": 'target6',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "full_path": "some/path/to/something.parquet"
                               }
                           ]}],
                "return": {
                    'target': 'target6',
                    'bucket_result': {'okay': True, 'err': None},
                    'full_path': (None, None, Exception),
                    'expected_result': {'success': None, 'failed_checks': [({
                                                                                "bucket_name": "bucket",
                                                                                "full_path": "some/path/to/something.parquet"
                                                                            }
                    , {'exception': Exception})]}
                }},
            'target7': {
                "input": [{"target_name": 'target7',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "prefix": "some/path/to/",
                                   "suffix": ".parquet",
                               }
                           ]}],
                "return": {
                    'target': 'target7',
                    'bucket_result': {'okay': True, 'err': None},
                    'contents': ([], 0,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'expected_result': {'failed_checks': [({"bucket_name": "bucket",
                                                            "prefix": "some/path/to/",
                                                            "suffix": ".parquet"},
                                                           {'no_file_found_s3': 's3://some/path/to/'})],
                                        'success': False}
                }
            },
            'target8': {
                "input": [{"target_name": 'target8',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "prefix": "some/path/to/",
                                   "suffix": ".parquet",
                                   "check_total_object": 5,
                                   "check_total_size_kb": 0.5
                               }
                           ]}],
                "return": {
                    'target': 'target8',
                    'bucket_result': {'okay': True, 'err': None},
                    'contents': (None, None, None, None, Exception),
                    'expected_result': {'success': None, 'failed_checks': [({"bucket_name": "bucket",
                                                                             "prefix": "some/path/to/",
                                                                             "suffix": ".parquet",
                                                                             "check_total_object": 5,
                                                                             "check_total_size_kb": 0.5},
                                                                            {'exception': Exception})],
                                        }}},
            'target9': {
                "input": [{"target_name": 'target9',
                           "items": [
                               {
                                   "bucket_name": "bucket",
                                   "prefix": "some/path/to/",
                                   "suffix": ".parquet",
                                   "check_total_object": 0,
                                   "check_total_size_kb": 1
                               }
                           ]}],
                "return": {
                    'target': 'target9',
                    'bucket_result': {'okay': True, 'err': None},
                    'contents': ([{'Size': None, 'Key': 'some/path/to/something.parquet'},
                                  {'Size': None, 'Key': 'some/path/to/something.parquet'},
                                  {'Size': None, 'Key': 'some/path/to/something.parquet'}], 3,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'prefix_suffix': (None, Exception),
                    'file_empty': (None, None, Exception),
                    'file_size': (None, None, Exception),
                    'expected_result': {'failed_checks': [({"bucket_name": "bucket",
                                                            "prefix": "some/path/to/",
                                                            "suffix": ".parquet",
                                                            "check_total_object": 0,
                                                            "check_total_size_kb": 1},
                                                           {'exception': [Exception, Exception, Exception]})],
                                        'success': None}
                }}
        }

    # def test_init_(self):

    @patch('watchmen.process.rorschach.Rorschach._process_checking')
    @patch('watchmen.process.rorschach.Rorschach._create_summary')
    @patch('watchmen.process.rorschach.Rorschach._create_result')
    @patch('watchmen.process.rorschach.Rorschach._load_config')
    def test_monitor(self, mock_config, mock_result, mock_summary, mock_checking):

        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)


        mock_config.return_value = self.example_config_file.get('Daily'), None
        mock_checking.return_value = self.process_checking_result
        mock_summary.return_value = self.create_summary_example
        mock_result.return_value = self.expected_return.get('TT')

        expected = mock_result()
        returned = rorschach_obj.monitor()
        self.assertEqual(expected, returned)

    def test_check_invalid_event(self):
        valid_event_tests = [
            self.example_event_hourly,
            self.example_event_daily
        ]
        for valid_event in valid_event_tests:
            rorschach_obj = Rorschach(event=valid_event, context=None)
            returned = rorschach_obj._check_invalid_event()
            self.assertFalse(returned)

        # Method should return true whenever the event passed in is invalid:
        for invalid_event in self.example_invalid_events:
            rorschach_obj = Rorschach(event=invalid_event, context=None)
            returned = rorschach_obj._check_invalid_event()
            self.assertTrue(returned)

    def test_create_invalid_event_results(self):

        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._create_invalid_event_results()

        # The date created and date updated attributes of the result object have to be set manually to properly compare
        # the expected and returned objects:
        email_result = returned[0].to_dict()
        email_result["dt_created"] = "2020-12-15T00:00:00+00:00"
        email_result["dt_updated"] = "2020-12-15T00:00:00+00:00"

        # Assert email result returned is correct:
        self.assertEqual(self.expected_invalid_event_email_result, email_result)

    @patch('builtins.open', new_callable=mock_open())
    @patch('watchmen.process.rorschach.yaml.load')
    def test_load_config(self, mock_file, mock_open):

        with mock_open as m:
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            mock_file.return_value = self.example_config_file
            expected = self.example_config_file.get('Daily')
            returned, returned_tb = rorschach_obj._load_config()
            self.assertEqual(expected, returned)
            self.assertEqual(None, returned_tb)

            mock_file.return_value = None
            mock_open.side_effect = Exception
            returned, returned_msg = rorschach_obj._load_config()
            self.assertEqual(None, returned)
            self.assertTrue(Exception, returned_msg)

    def test_create_config_not_load_results(self):
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        s3_target = (None, 's3_config.yaml')
        returned = rorschach_obj._create_config_not_load_results(s3_target)
        # The date created and date updated attributes of the result object have to be set manually to properly compare
        # the expected and returned objects:
        email_result = returned[0].to_dict()
        email_result["dt_created"] = "2020-12-15T00:00:00+00:00"
        email_result["dt_updated"] = "2020-12-15T00:00:00+00:00"

        self.assertEqual(self.expected_invalid_config_file_result, email_result)

    @patch('watchmen.process.rorschach.Rorschach._generate_contents')
    @patch('watchmen.process.rorschach._s3.check_bucket')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file_existence')
    @patch('watchmen.process.rorschach.Rorschach._check_most_recent_file')
    @patch('watchmen.process.rorschach.Rorschach._check_file_prefix_suffix')
    @patch('watchmen.process.rorschach.Rorschach._check_file_empty')
    @patch('watchmen.process.rorschach.Rorschach._compare_total_file_size_to_threshold')
    def test_process_checking(self, mock_file_size, mock_file_empty, mock_key_match, mock_recent, mock_full_path,
                              mock_bucket, mock_contents):

        for key in self.result:
            result = self.result.get(key).get('return')
            mock_bucket.return_value = result.get('bucket_result')
            mock_full_path.return_value = result.get('full_path')
            mock_contents.return_value = result.get('contents')
            mock_recent.return_value = result.get('recent_contents')
            mock_key_match.return_value = result.get('prefix_suffix')
            mock_file_size.return_value = result.get('file_size')
            mock_file_empty.return_value = result.get('file_empty')

            expected = {key: result.get('expected_result')}
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._process_checking(self.result.get(key).get('input'))
            self.assertEqual(returned, expected)

    def test_create_summary(self):

        # This only tests the successful case, which need more test cases
        result = self.result.get('target2').get('return')
        process_summary = {'target2': result.get('expected_result')}
        summary_details = [{
            "message": MESSAGES.get("failure_message").format('target2'),
            "success": False,
            "subject": MESSAGES.get("failure_subject").format('target2'),
            "details": 'The following S3 paths failed their checks:\n'
             'There is at least one key did not match the expected prefix: '
             'some/path/to/ and suffix: .parquet.\n'
             'This file: some/path/to/something.parquet is empty for target '
             'data in S3.\n'
             'The size of all files founded in s3://some/path/to/ is 0.2 KB, '
             'which is less than expected total file size 0.5 KB.\n'
             'The number of objects founded in s3://some/path/to/ is 3, which '
             'is less than expected total objects count 5.\n'
             '\n'
             '\n',
            "target": 'target2'
        }]

        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._create_summary(process_summary)
        self.assertEqual(returned, summary_details)

    def test_create_result(self):

        for key in self.expected_return:
            example_summary = self.expected_result[key]
            example_result = self.expected_return[key]
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._create_result(example_summary)
            emp = []
            for obj in returned:
                obj = obj.to_dict()
                obj['dt_created'] = '2020-12-15T00:00:00+00:00'
                obj['dt_updated'] = '2020-12-15T00:00:00+00:00'
                emp.append(obj)
            self.assertEqual(emp, example_result)

    def test_generate_key(self):
        prefix_format = 'some/path/year=%0Y/month=%0m/day=%0d/'
        check_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(**{'days': 1})
        expected = (check_time.strftime(prefix_format), None)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        event = self.example_event_daily.get('Type')
        returned = rorschach_obj._generate_key(prefix_format, event)
        self.assertEqual(expected, returned)

    def test_check_file_prefix_suffix(self):
        suffix = '.parquet'
        prefix = 'some/path/to/'
        expected = (True, None)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_file_prefix_suffix(self.example_contents, suffix, prefix)
        self.assertEqual(expected, returned)


    def test_check_file_empty(self):
        expected = (True, ['some/path/to/something.json'], None)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_file_empty(self.example_contents)
        self.assertEqual(expected, returned)

    def test_compare_total_file_size_to_threshold(self):
        con_total_size = 0.4
        expected = (True, 0.3, None)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._compare_total_file_size_to_threshold(self.example_contents, con_total_size)
        self.assertEqual(expected, returned)


    def test_check_most_recent_file(self):

        check_most_recent_file = 2
        expected = [self.example_contents[3], self.example_contents[2]]
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_most_recent_file(self.example_contents, check_most_recent_file)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.rorschach.Rorschach._generate_key')
    @patch('watchmen.process.rorschach._s3.generate_pages')
    def test_generate_contents(self, mock_pages, mock_key):

        item = self.example_config_file.get('Daily')[0].get('items')[0]
        self.rr = 'some/path/to/', None
        mock_key.return_value = self.rr
        ex_full_path = 's3://' + 'bucket' + '/' + 'some/path/to/'
        ex_prefix_generate = 'some/path/to/'
        ex_contents = self.example_contents
        mock_pages.return_value = self.example_contents
        ex_count = 4
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        re_contents, re_count, re_prefix_generate, re_full_path, re_tb = rorschach_obj._generate_contents(item)

        self.assertEqual(re_contents, ex_contents)
        self.assertEqual(re_count, ex_count)
        self.assertEqual(re_prefix_generate, ex_prefix_generate)
        self.assertEqual(re_full_path, ex_full_path)
        self.assertEqual(re_tb, None)
