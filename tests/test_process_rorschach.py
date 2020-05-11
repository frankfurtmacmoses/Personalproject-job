import datetime
from mock import patch, mock_open
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
            'details': 'Cannot load S3 targets from file:\ns3_config.yaml\nException: s3_config.yaml',
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
                    "target_name": "target2",
                    "items": [
                        {
                            "bucket_name": "bucket",
                            "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                            "suffix": ".parquet"
                        }
                    ]
                }
            ]}
        self.process_checking_result = {"target1": [], "target2": []}
        self.example_checking_cases = {
            "success": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                        "check_total_object": 1,
                        "check_total_size_kb": 0.1
                    }
                ]
            },
            "fail_file_not_found": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet"
                    }
                ]
            },
            "fail_key_not_match": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet"
                    }
                ]
            },
            "fail_file_size_count": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                        "check_total_object": 4,
                        "check_total_size_kb": 0.3
                    }
                ]
            },
            "single_file_success": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "full_path": "some/path/to/something.parquet"
                    }
                ]},
            "single_file_fail": {
                "target_name": "target1",
                "items": [
                    {
                        "bucket_name": "bucket",
                        "full_path": "some/path/to/something.parquet"
                    }
                ]}
        }
        self.example_checking_results = {
            "success": {
                'target': 'target1',
                'keys': 'some/path/to/',
                'pages': [{'Size': 100, 'Key': 'some/path/to/something.parquet'},
                          {'Size': 100, 'Key': 'some/path/to/something.parquet'}],
                'prefix_suffix': False,
                'file_empty': (False, []),
                'file_size': (False, 200),
                'expected_result': []
            },
            "fail_file_not_found": {
                'target': 'target1',
                'keys': 'some/path/to/',
                'pages': [],
                'expected_result': [{'no_file_found_s3': 's3://bucket/some/path/to/'}]
            },
            "fail_key_not_match": {
                'target': 'target1',
                'keys': 'some/path/to/',
                'pages': [{'Size': 100, 'Key': 'some/path/to/something.json'}],
                'expected_result': [{'object_key_not_match': (True, 1)}]
            },
            "fail_file_size_count": {
                'target': 'target1',
                'keys': 'some/path/to/',
                'pages': [{'Size': 100, 'Key': 'some/path/to/something.parquet'},
                          {'Size': 100, 'Key': 'some/path/to/something.parquet'},
                          {'Size': 0, 'Key': 'some/path/to/something.parquet'}],
                'prefix_suffix': False,
                'file_empty': (True, ['some/path/to/something.parquet']),
                'file_size': (False, 0.2),
                'expected_result': [{'at_least_one_file_empty': (True, ['some/path/to/something.parquet'])},
                                    {'file_size_too_less': ('s3://bucket/some/path/to/', 0.2, 0.3)},
                                    {'count_object_too_less': ('s3://bucket/some/path/to/', 3, 4)}]
            },
            "single_file_success": {
                'target': 'target1',
                'valid': True,
                'keys': 'some/path/to/something.parquet',
                'pages': [{'Size': 100, 'Key': 'some/path/to/something.parquet'}],
                'full_path_result': [False, 'bucket/some/path/to/something.parquet'],
                'expected_result': []
            },
            "single_file_fail": {
                'target': 'target1',
                'valid': False,
                'keys': 'some/path/to/something.parquet',
                'pages': [{'Size': 100, 'Key': 'some/path/to/some.parquet'}],
                'full_path_result': [True, 'some/path/to/something.parquet'],
                'expected_result': [
                    {'no_file_found_s3': 'some/path/to/something.parquet'}]
            }
        }
        self.example_success_summary = {
            "success": True,
            "subject": MESSAGES.get("success_subject").format("target1"),
            "details": MESSAGES.get("success_details").format("target1"),
            "message": MESSAGES.get("success_message").format("target1"),
            "target": "target1"
        }
        self.create_summary_example = [self.example_success_summary,
                                       self.example_success_summary]
        self.example_process_results = {
            'target1': [],
            'target2': [
                {'object_key_not_match': (True, 1)},
                {'at_least_one_file_empty': (True,
                                             ['some/path/to/something.parquet'])},
                {'file_size_too_less': (
                    's3://bucket/some/path/to/', 0.2, 0.3)},
                {'count_object_too_less':
                     ('s3://bucket/some/path/to/', 2, 3)}],
            'target3': [
                {'no_file_found_s3': 'some/path/to/something.zip'}]}

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

        self.example_contents = [{'Key': 'some/path/to/something.parquet', 'Size': 100},
                                 {'Key': 'some/path/to/something.parquet', 'Size': 100},
                                 {'Key': 'some/path/to/something.parquet', 'Size': 100},
                                 {'Key': 'some/path/to/something.json', 'Size': 0}]

    # def test_init_(self):

    @patch('watchmen.process.rorschach.Rorschach._load_config')
    @patch('watchmen.process.rorschach.Rorschach._process_checking')
    @patch('watchmen.process.rorschach.Rorschach._create_summary')
    @patch('watchmen.process.rorschach.Rorschach._create_result')
    def test_monitor(self, mock_result, mock_summary, mock_checking, mock_config):

        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)

        mock_config.return_values = self.example_config_file.get('Daily')
        mock_checking.return_values = self.process_checking_result
        mock_summary.return_values = self.create_summary_example
        mock_result.return_values = self.expected_return.get('TT')

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
            returned = rorschach_obj._load_config(self.example_config_path)
            m.assert_called_with('../watchmen/process/s3_config.yaml')

        mock_open.side_effect = Exception
        returned, returned_msg = rorschach_obj._load_config(self.example_config_path)
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

    @patch('watchmen.process.rorschach._s3.generate_pages')
    @patch('watchmen.process.rorschach.Rorschach._generate_key')
    @patch('watchmen.process.rorschach._s3.validate_file_on_s3')
    @patch('watchmen.process.rorschach._s3.check_bucket')
    def test_process_checking(self, mock_bucket, mock_valid, mock_keys, mock_pages):

        for key in self.example_checking_cases:
            target = [self.example_checking_cases[key]]
            result = self.example_checking_results[key]
            mock_bucket.return_value = {'okay': True, 'err': None}
            mock_valid.return_value = result.get('valid')
            mock_keys.return_value = result.get('keys')
            mock_pages.return_value = result.get('pages')
            expected = {result.get('target'): result.get('expected_result')}
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._process_checking(target)
            self.assertEqual(returned, expected)

    def test_create_summary(self):
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._create_summary(self.example_process_results)
        self.assertEqual(returned, self.example_summary_results)

        returned_exception = rorschach_obj._create_summary(self.example_process_ex_results)
        self.assertEqual(returned_exception, self.example_summary_ex_results)

    def test_create_result(self):
        for key in self.expected_return:
            example_summary = self.expected_result[key]
            example_result = self.expected_return[key]
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._create_result(example_summary)
            emp = []
            for obj in returned:
                obj = obj.to_dict()
                obj['dt_created'] = '2020-12-15T00:00:00+00:00'  # '2020-12-15T00:00:00+00:00'
                obj['dt_updated'] = '2020-12-15T00:00:00+00:00'  # '2020-12-15T00:00:00+00:00'
                emp.append(obj)
            self.assertEqual(emp, example_result)

    def test_generate_key(self):
        prefix_format = 'some/path/year=%0Y/month=%0m/day=%0d/'
        check_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(**{'days': 1})
        expected = check_time.strftime(prefix_format)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        event = self.example_event_daily.get('Type')
        returned = rorschach_obj._generate_key(prefix_format, event)
        self.assertEqual(expected, returned)

    def test_check_file_prefix_suffix(self):
        suffix = '.parquet'
        prefix = 'some/path/to/'
        expected = True
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_file_prefix_suffix(self.example_contents, suffix, prefix)
        self.assertEqual(expected, returned)

    def test_check_file_empty(self):
        expected = (True, ['some/path/to/something.json'])
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_file_empty(self.example_contents)
        self.assertEqual(expected, returned)

    def test_check_file_size_too_less(self):
        con_total_size = 0.4
        expected = (True, 0.3)
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_file_size_too_less(self.example_contents, con_total_size)
        self.assertEqual(expected, returned)
