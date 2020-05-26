import datetime
from mock import patch, mock_open
import pytz
import unittest

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
        self.example_traceback = 'Traceback'
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
            "Daily": [{
                "target_name": "target1",
                "items": [{
                    "bucket_name": "bucket",
                    "prefix": "dns-logs-others/customer=302886/year=%0Y/month=%0m/day=%0d/",
                    "suffix": ".parquet"
                }]
            }]
        }
        self.example_process_checking_result = {
            "target1": []
        }
        self.example_create_summary_result = [{
            "success": True,
            "subject": MESSAGES.get("success_subject").format("target1"),
            "details": MESSAGES.get("success_details").format("target1"),
            "message": MESSAGES.get("success_message").format("target1"),
            "target": "target1"
        }]
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
        self.example_process_checking_cases  = {
            'success_multi_items': {
                "input": [{
                    "target_name": 'target1',
                    "items": [{
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                        "check_total_object": 1,
                        "check_total_size_kb": 0,
                        "check_most_recent_file": 2
                    }]
                }],
                "return": {
                    'target': 'target1',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'contents': ([{
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }], 3, 'some/path/to/', 's3://some/path/to/', None),
                    'recent_contents': ([{
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }], 2),
                    'prefix_suffix': (True, None),
                    'file_empty': (False, [], None),
                    'file_size': (True, 0.2, None)
                }
            },
            'fail_items': {
                "input": [{
                    "target_name": 'target2',
                    "items": [{
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                        "check_total_object": 5,
                        "check_total_size_kb": 0.5
                    }]
                }],
                "return": {
                    'target': 'target2',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'contents': ([{
                        'Size': 100,
                        'Key': 'some/path/to/something.json'
                    }, {
                        'Size': 100,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': 0,
                        'Key': 'some/path/to/something.parquet'
                    }], 3,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'prefix_suffix': (False, None),
                    'file_empty': (True, ['some/path/to/something.parquet'], None),
                    'file_size': (True, 0.2, None)
                }
            },
            'fail_found_bucket': {
                "input": [{
                    "target_name": 'target3',
                    "items": [{
                        "bucket_name": "bucket",
                        'prefix': 'some/path/to'
                    }]
                }],
                "return": {
                    'target': 'target3',
                    'bucket_result': {
                        'okay': False,
                        'err': None
                    }
                }
            },
            'ex_found_bucket': {
                "input": [{
                    "target_name": 'target4',
                    "items": [{
                        "bucket_name": "bucket",
                        'prefix': 'some/path/to'
                    }]
                }],
                "return": {
                    'target': 'target4',
                    'bucket_result': {
                        'okay': None,
                        'err': Exception
                    }
                }
            },
            'fail_full_path': {
                "input": [{
                    "target_name": 'target5',
                    "items": [{
                        "bucket_name": "bucket",
                        "full_path": "some/path/to/something.parquet"
                    }]
                }],
                "return": {
                    'target': 'target5',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'full_path': (False, "s3://bucket/some/path/to/something.parquet", None)
                }
            },
            'ex_full_path': {
                "input": [{
                    "target_name": 'target6',
                    "items": [{
                        "bucket_name": "bucket",
                        "full_path": "some/path/to/something.parquet"
                    }]
                }],
                "return": {
                    'target': 'target6',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'full_path': (None, None, Exception)
                }
            },
            'fail_contents': {
                "input": [{
                    "target_name": 'target7',
                    "items": [{
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                    }]
                }],
                "return": {
                    'target': 'target7',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'contents': ([], 0,
                                 'some/path/to/',
                                 's3://some/path/to/', None)
                }
            },
            'ex_contents': {
                "input": [{
                    "target_name": 'target8',
                    "items": [{
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet"
                    }]
                }],
                "return": {
                    'target': 'target8',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'contents': (None, None, None, None, Exception)
                }
            },
            'ex_multi_items': {
                "input": [{
                    "target_name": 'target9',
                    "items": [{
                        "bucket_name": "bucket",
                        "prefix": "some/path/to/",
                        "suffix": ".parquet",
                        "check_total_object": 0,
                        "check_total_size_kb": 1
                    }]
                }],
                "return": {
                    'target': 'target9',
                    'bucket_result': {
                        'okay': True,
                        'err': None
                    },
                    'contents': ([{
                        'Size': None,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': None,
                        'Key': 'some/path/to/something.parquet'
                    }, {
                        'Size': None,
                        'Key': 'some/path/to/something.parquet'
                    }], 3,
                                 'some/path/to/',
                                 's3://some/path/to/', None),
                    'prefix_suffix': (None, Exception),
                    'file_empty': (None, None, Exception),
                    'file_size': (None, None, Exception),
                }
            }
        }
        self.example_process_checking_results = {
            'success_multi_items': {
                'target1': {
                    'success': True,
                    'failed_checks': []
                }
            },
            'fail_items': {
                'target2': {
                    'success': False,
                    'failed_checks': [
                        ({
                             "bucket_name": "bucket",
                             "prefix": "some/path/to/",
                             "suffix": ".parquet",
                             "check_total_object": 5,
                             "check_total_size_kb": 0.5
                         }, {
                             'at_least_one_file_empty': (True, ['some/path/to/something.parquet']),
                             'count_object_too_less': ('s3://some/path/to/', 3, 5),
                             'prefix_suffix_not_match': ('some/path/to/',
                                                         '.parquet'),
                             'total_file_size_below_threshold': (
                                 's3://some/path/to/', 0.2, 0.5)
                         })
                    ]
                }
            },
            'fail_found_bucket': {
                'target3': {
                    'success': False,
                    'failed_checks': [({
                                           'bucket_name': 'bucket',
                                           'prefix': 'some/path/to'
                                       }, {
                                           'bucket_not_found': 's3://{}'.format(
                                               'bucket')
                                       })]
                }
            },
            'ex_found_bucket': {
                'target4': {
                    'success': None,
                    'failed_checks': [({
                                           'bucket_name': 'bucket',
                                           'prefix': 'some/path/to'
                                       }, {
                                           'exception': Exception
                                       })]
                }
            },
            'fail_full_path': {
                'target5': {
                    'success': False,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "full_path": "some/path/to/something.parquet"
                                       }, {
                                           'no_file_found_s3': "s3://bucket/some/path/to/something.parquet"
                                       })]
                }
            },
            'ex_full_path': {
                'target6': {
                    'success': None,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "full_path": "some/path/to/something.parquet"
                                       }, {
                                           'exception': Exception
                                       })]
                }
            },
            'fail_contents': {
                'target7': {
                    'success': False,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "prefix": "some/path/to/",
                                           "suffix": ".parquet"
                                       }, {
                                           'no_file_found_s3': 's3://some/path/to/'
                                       })]
                }
            },
            'ex_contents': {
                'target8': {
                    'success': None,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "prefix": "some/path/to/",
                                           "suffix": ".parquet"
                                       }, {
                                           'exception': Exception
                                       })]
                }
            },
            'ex_multi_items': {
                'target9': {
                    'success': None,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "prefix": "some/path/to/",
                                           "suffix": ".parquet",
                                           "check_total_object": 0,
                                           "check_total_size_kb": 1
                                       },
                                       {
                                           'exception': [Exception, Exception, Exception]
                                       })]
                }
            },
            'fail_ex_items': {
                'target10': {
                    'success': False,
                    'failed_checks': [({
                                           "bucket_name": "bucket",
                                           "prefix": "some/path/to/",
                                           "suffix": ".parquet",
                                           "check_total_object": 0,
                                           "check_total_size_kb": 1
                                       },
                                       {
                                           'exception': [Exception],
                                           'at_least_one_file_empty': (True, ['some/path/to/something.parquet'])
                                       })]
                }
            }
        }
        self.example_create_summary_results = {
            'success_multi_items': [{
                "message": MESSAGES.get("success_message").format('target1'),
                "success": True,
                "subject": MESSAGES.get("success_subject").format('target1'),
                "details": MESSAGES.get("success_details").format('target1'),
                "target": 'target1'
            }],
            'fail_items': [{
                "message": MESSAGES.get("failure_message").format('target2'),
                "success": False,
                "subject": MESSAGES.get("failure_subject").format('target2'),
                "details": (MESSAGES.get('failure_details').format(
                    MESSAGES.get('failure_prefix_suffix_not_match').format('some/path/to/', '.parquet') +
                    MESSAGES.get('failure_file_empty').format('some/path/to/something.parquet') +
                    MESSAGES.get('failure_total_file_size_below_threshold').format('s3://some/path/to/', 0.2, 0.5) +
                    MESSAGES.get('failure_count_too_less').format('s3://some/path/to/', 3, 5)) + '\n\n'),
                "target": 'target2'
            }],
            'fail_found_bucket': [{
                "message": MESSAGES.get("failure_message").format('target3'),
                "success": False,
                "subject": MESSAGES.get("failure_subject").format('target3'),
                "details": (MESSAGES.get('failure_details').format(
                    MESSAGES.get('failure_bucket_not_found').format('bucket')) + '\n\n'),
                "target": 'target3'
            }],
            'ex_found_bucket': [{
                "message": MESSAGES.get("exception_message"),
                "success": None,
                "subject": MESSAGES.get("exception_checking_subject").format('target4'),
                "details": MESSAGES.get('exception_details').format(
                    '{}{}: {}\n'.format('bucket', 'some/path/to', Exception)),
                "target": 'target4'
            }],
            'fail_full_path': [{
                "message": MESSAGES.get("failure_message").format('target5'),
                "success": False,
                "subject": MESSAGES.get("failure_subject").format('target5'),
                "details": (MESSAGES.get('failure_details').format(
                    MESSAGES.get('failure_no_file_found_s3').format('some/path/to/something.parquet')) + '\n\n'),
                "target": 'target5'
            }],
            'fail_ex_items': [{
                "message": MESSAGES.get("failure_message").format('target10'),
                "success": False,
                "subject": MESSAGES.get("failure_subject").format('target10'),
                "details": ((MESSAGES.get('failure_details').format(MESSAGES.get('failure_file_empty').format(
                    'some/path/to/something.parquet')) + '\n\n') + MESSAGES.get('exception_details').format(
                    'bucket/some/path/to/: {}\n'.format(Exception))),
                "target": 'target10'
            }]
        }
        self.example_state_cases = {
            'T': [{
                'success': True,
                'subject': 'Rorschach Success',
                'details': 'some details',
                'message': 'some message',
                'target': 'target 1'
            }, {
                'details': 'some details',
                'disable_notifier': True,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'dt_updated': '2020-12-15T00:00:00+00:00',
                'is_ack': False,
                'is_notified': False,
                'message': 'some message',
                'result_id': 0,
                'snapshot': None,
                'source': 'Rorschach',
                'state': 'SUCCESS',
                'subject': 'Rorschach Success',
                'success': True,
                'target': 'target 1'
            }],
            'F': [{
                'success': False,
                'subject': 'Rorschach Failure',
                'details': 'some details',
                'message': 'some message',
                'target': 'target 1'
            }, {
                'details': 'some details',
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'dt_updated': '2020-12-15T00:00:00+00:00',
                'is_ack': False,
                'is_notified': False,
                'message': 'some message',
                'result_id': 0,
                'snapshot': None,
                'source': 'Rorschach',
                'state': 'FAILURE',
                'subject': 'Rorschach Failure',
                'success': False,
                'target': 'target 1'
            }],
            'E': [{
                'success': None,
                'subject': 'Rorschach Exception',
                'details': 'some details',
                'message': 'some message',
                'target': 'target 1'
            }, {
                'details': 'some details',
                'disable_notifier': False,
                'dt_created': '2020-12-15T00:00:00+00:00',
                'dt_updated': '2020-12-15T00:00:00+00:00',
                'is_ack': False,
                'is_notified': False,
                'message': 'some message',
                'result_id': 0,
                'snapshot': None,
                'source': 'Rorschach',
                'state': 'EXCEPTION',
                'subject': 'Rorschach Exception',
                'success': None,
                'target': 'target 1'
            }]
        }
        self.example_state_cases_summary = {
            'TT': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('T')[0]
                   ],
            'TF': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('F')[0]
                   ],
            'TE': [self.example_state_cases.get('T')[0],
                   self.example_state_cases.get('E')[0]
                   ],
            'EF': [self.example_state_cases.get('F')[0],
                   self.example_state_cases.get('E')[0]
                   ]
        }
        self.example_create_results = {
            'TT': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('T')[1], {
                       'details': 'Rorschach Success\nsome details\n\nRorschach Success\nsome details\n\n',
                       'disable_notifier': True,
                       'dt_created': '2020-12-15T00:00:00+00:00',
                       'dt_updated': '2020-12-15T00:00:00+00:00',
                       'is_ack': False,
                       'is_notified': False,
                       'message': MESSAGES.get("success_message").format('All targets'),
                       'result_id': 0,
                       'snapshot': None,
                       'source': 'Rorschach',
                       'state': 'SUCCESS',
                       'subject': MESSAGES.get("generic_suceess_subject"),
                       'success': True,
                       'target': 'Generic S3'
                   }
                   ],
            'TF': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('F')[1], {
                       'details': 'Rorschach Success\nsome details\n\nRorschach Failure\nsome details\n\n',
                       'disable_notifier': False,
                       'dt_created': '2020-12-15T00:00:00+00:00',
                       'dt_updated': '2020-12-15T00:00:00+00:00',
                       'is_ack': False,
                       'is_notified': False,
                       'message': MESSAGES.get("failure_message"),
                       'result_id': 0,
                       'snapshot': None,
                       'source': 'Rorschach',
                       'state': 'FAILURE',
                       'subject': MESSAGES.get("generic_failure_subject"),
                       'success': False,
                       'target': 'Generic S3'
                   }
                   ],
            'TE': [self.example_state_cases.get('T')[1],
                   self.example_state_cases.get('E')[1], {
                       'details': 'Rorschach Success\nsome details\n\nRorschach Exception\nsome details\n\n',
                       'disable_notifier': False,
                       'dt_created': '2020-12-15T00:00:00+00:00',
                       'dt_updated': '2020-12-15T00:00:00+00:00',
                       'is_ack': False,
                       'is_notified': False,
                       'message': MESSAGES.get("exception_message"),
                       'result_id': 0,
                       'snapshot': None,
                       'source': 'Rorschach',
                       'state': 'EXCEPTION',
                       'subject': MESSAGES.get("generic_exception_subject"),
                       'success': None,
                       'target': 'Generic S3'
                   }
                   ],
            'EF': [self.example_state_cases.get('F')[1],
                   self.example_state_cases.get('E')[1], {
                       'details': 'Rorschach Failure\nsome details\n\nRorschach Exception\nsome details\n\n',
                       'disable_notifier': False,
                       'dt_created': '2020-12-15T00:00:00+00:00',
                       'dt_updated': '2020-12-15T00:00:00+00:00',
                       'is_ack': False,
                       'is_notified': False,
                       'message': MESSAGES.get("exception_message") + MESSAGES.get("failure_message"),
                       'result_id': 0,
                       'snapshot': None,
                       'source': 'Rorschach',
                       'state': 'EXCEPTION',
                       'subject': MESSAGES.get("generic_fail_exception_subject"),
                       'success': None,
                       'target': 'Generic S3'
                   }
                   ]
        }

    # def test_init_(self):

    @patch('watchmen.process.rorschach.Rorschach._process_checking')
    @patch('watchmen.process.rorschach.Rorschach._create_summary')
    @patch('watchmen.process.rorschach.Rorschach._create_result')
    @patch('watchmen.process.rorschach.Rorschach._load_config')
    @patch('watchmen.process.rorschach.Rorschach._check_invalid_event')
    def test_monitor(self, mock_event, mock_config, mock_result, mock_summary, mock_checking):
        """
        test watchmen.process.rorschach :: Rorschach :: monitor
        """

        # check a success case
        mock_event.return_value = False
        mock_config.return_value = self.example_config_file.get('Daily'), None
        mock_checking.return_value = self.example_process_checking_result
        mock_summary.return_value = self.example_create_summary_result
        mock_result.return_value = self.example_create_results.get('TT')
        expected = mock_result()
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj.monitor()
        self.assertEqual(expected, returned)

        # check a case with invalid event
        mock_event.return_value = True
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj.monitor()
        returned = returned[0].to_dict()
        returned['dt_created'] = '2020-12-15T00:00:00+00:00'
        returned['dt_updated'] = '2020-12-15T00:00:00+00:00'
        self.assertEqual(self.expected_invalid_event_email_result, returned)

        # check a case with s3 target file not loaded
        mock_event.return_value = False
        mock_config.return_value = None, (None, 's3_config.yaml')
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj.monitor()
        returned = returned[0].to_dict()
        returned['dt_created'] = '2020-12-15T00:00:00+00:00'
        returned['dt_updated'] = '2020-12-15T00:00:00+00:00'
        self.assertEqual(self.expected_invalid_config_file_result, returned)

    def test_check_invalid_event(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_invalid_event
        """
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
        """
        test watchmen.process.rorschach :: Rorschach :: _create_invalid_event_results
        """

        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._create_invalid_event_results()
        returned = returned[0].to_dict()
        returned["dt_created"] = "2020-12-15T00:00:00+00:00"
        returned["dt_updated"] = "2020-12-15T00:00:00+00:00"
        self.assertEqual(self.expected_invalid_event_email_result, returned)

    @patch('builtins.open', new_callable=mock_open())
    @patch('watchmen.process.rorschach.yaml.load')
    def test_load_config(self, mock_file, mock_open):
        """
        test watchmen.process.rorschach :: Rorschach :: _load_config
        """

        with mock_open:
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
        """
        test watchmen.process.rorschach :: Rorschach :: _create_config_not_load_results
        """

        s3_target = (None, 's3_config.yaml')
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._create_config_not_load_results(s3_target)
        returned = returned[0].to_dict()
        returned["dt_created"] = "2020-12-15T00:00:00+00:00"
        returned["dt_updated"] = "2020-12-15T00:00:00+00:00"
        self.assertEqual(self.expected_invalid_config_file_result, returned)

    @patch('watchmen.process.rorschach.Rorschach._generate_contents')
    @patch('watchmen.process.rorschach._s3.check_bucket')
    @patch('watchmen.process.rorschach.Rorschach._check_single_file_existence')
    @patch('watchmen.process.rorschach.Rorschach._check_most_recent_file')
    @patch('watchmen.process.rorschach.Rorschach._check_file_prefix_suffix')
    @patch('watchmen.process.rorschach.Rorschach._check_file_empty')
    @patch('watchmen.process.rorschach.Rorschach._compare_total_file_size_to_threshold')
    def test_process_checking(self, mock_file_size, mock_file_empty, mock_key_match, mock_recent, mock_full_path,
                              mock_bucket, mock_contents):
        """
        test watchmen.process.rorschach :: Rorschach :: _process_checking
        """
        for key in self.example_process_checking_cases :
            input = self.example_process_checking_cases .get(key).get('input')  # input each edge case for processing checking
            mock_result = self.example_process_checking_cases .get(key).get('return')  # the expected mock results of each edge case

            mock_bucket.return_value = mock_result.get('bucket_result')
            mock_full_path.return_value = mock_result.get('full_path')
            mock_contents.return_value = mock_result.get('contents')
            mock_recent.return_value = mock_result.get('recent_contents')
            mock_key_match.return_value = mock_result.get('prefix_suffix')
            mock_file_size.return_value = mock_result.get('file_size')
            mock_file_empty.return_value = mock_result.get('file_empty')

            expected = self.example_process_checking_results.get(key)
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._process_checking(input)
            self.assertEqual(returned, expected)

    def test_create_summary(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_summary
        """
        for key in self.example_create_summary_results:
            input = self.example_process_checking_results.get(key)  # input each edge case for creating summary

            expected = self.example_create_summary_results.get(key)
            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._create_summary(input)
            self.assertEqual(returned, expected)

    def test_create_result(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _create_result
        """
        for key in self.example_create_results:
            summary = self.example_state_cases_summary[key]
            result = self.example_create_results[key]

            rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
            returned = rorschach_obj._create_result(summary)
            example_result_list = []
            for obj in returned:
                obj = obj.to_dict()
                obj['dt_created'] = '2020-12-15T00:00:00+00:00'
                obj['dt_updated'] = '2020-12-15T00:00:00+00:00'
                example_result_list.append(obj)
            self.assertEqual(example_result_list, result)

    def test_generate_key(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _generate_key
        """

        prefix_format = 'some/path/year=%0Y/month=%0m/day=%0d/'
        check_time = datetime.datetime.now(pytz.utc) - datetime.timedelta(**{'days': 1})

        # test the Try case
        expected, expected_tb = check_time.strftime(prefix_format), None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_tb = rorschach_obj._generate_key(prefix_format, self.example_event_daily.get('Type'))
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # test the Exception case
        expected, expected_tb = None, 'Traceback'
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_tb = rorschach_obj._generate_key(None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(expected_tb in returned_tb)

    @patch('watchmen.process.rorschach.Rorschach._generate_key')
    @patch('watchmen.process.rorschach._s3.generate_pages')
    def test_generate_contents(self, mock_pages, mock_key):
        """
        test watchmen.process.rorschach :: Rorschach :: _generate_contents
        """

        item = self.example_config_file.get('Daily')[0].get('items')[0]
        mock_key.return_value = 'some/path/to/', None
        mock_pages.return_value = self.example_contents
        expected_contents, expected_count, expected_prefix, expected_path, expected_tb = \
            self.example_contents, 4, 'some/path/to/', 's3://bucket/some/path/to/',  None
        # test the Try case without offset
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned_contents, returned_count, returned_prefix, returned_path, returned_tb = \
            rorschach_obj._generate_contents(item)
        self.assertEqual((expected_contents, expected_count, expected_prefix, expected_path, expected_tb),
                         (returned_contents, returned_count, returned_prefix, returned_path, returned_tb))

        # test the Try case with offset
        item.update({'offset': 2})
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned_contents, returned_count, returned_prefix, returned_path, returned_tb = \
            rorschach_obj._generate_contents(item)
        self.assertEqual((expected_contents, expected_count, expected_prefix, expected_path, expected_tb),
                         (returned_contents, returned_count, returned_prefix, returned_path, returned_tb))

        # test the Exception case
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned_contents, returned_count, returned_prefix, returned_path, returned_tb = \
            rorschach_obj._generate_contents(None)
        self.assertEqual((None, None, None, None), (returned_contents, returned_count, returned_prefix, returned_path))
        self.assertTrue(self.example_traceback in returned_tb)

    @patch('watchmen.process.rorschach._s3.validate_file_on_s3')
    @patch('watchmen.process.rorschach.Rorschach._generate_key')
    def test_check_single_file_existence(self, mock_key, mock_valid):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_single_file_existence
        """

        mock_key.return_value = 'some/path/to/something.parquet', None
        mock_valid.return_value = True
        item = self.example_process_checking_cases .get('fail_full_path').get('input')[0].get('items')[0]
        expected, expected_path, expected_tb = True, 'some/path/to/something.parquet', None

        # test the Try case without offset key
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_path, returned_tb = rorschach_obj._check_single_file_existence(item)
        self.assertEqual((expected, expected_path, expected_tb), (returned, returned_path, returned_tb))

        # test the Try case with offset key
        item.update({'offset': 2})
        returned, returned_path, returned_tb = rorschach_obj._check_single_file_existence(item)
        self.assertEqual((expected, expected_path, expected_tb), (returned, returned_path, returned_tb))

        # test the Exception case
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_path, returned_tb = rorschach_obj._check_single_file_existence(None)
        self.assertEqual((None, None), (returned, returned_path))
        self.assertTrue(self.example_traceback in returned_tb)

    def test_check_most_recent_file(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_most_recent_file
        """
        check_most_recent_file = 2
        expected = [self.example_contents[3], self.example_contents[2]]
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned = rorschach_obj._check_most_recent_file(self.example_contents, check_most_recent_file)
        self.assertEqual(expected, returned)

    def test_check_file_prefix_suffix(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_file_prefix_suffix
        """
        suffix = '.parquet'
        prefix = 'some/path/to/'

        # test the Try case
        expected, expected_tb = False, None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_tb = rorschach_obj._check_file_prefix_suffix(self.example_contents, suffix, prefix)
        self.assertEqual((expected, expected_tb), (returned, returned_tb))

        # test the Exception case
        expected = None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_tb = rorschach_obj._check_file_prefix_suffix(None, None, None)
        self.assertEqual(expected, returned)
        self.assertTrue(self.example_traceback in returned_tb)

    def test_check_file_empty(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _check_file_empty
        """

        # test the Try case
        expected, expected_path, expected_tb = True, ['some/path/to/something.json'], None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_path, returned_tb = rorschach_obj._check_file_empty(self.example_contents)
        self.assertEqual((expected, expected_path, expected_tb), (returned, returned_path, returned_tb))

        # test the Exception case
        expected, expected_path = None, None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_path, returned_tb = rorschach_obj._check_file_empty(None)
        self.assertEqual((expected, expected_path), (returned, returned_path))
        self.assertTrue(self.example_traceback in returned_tb)

    def test_compare_total_file_size_to_threshold(self):
        """
        test watchmen.process.rorschach :: Rorschach :: _compare_total_file_size_to_threshold
        """
        con_total_size = 0.4

        # test the Try case
        expected, expected_count, expected_tb = True, 0.3, None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_count, returned_tb = rorschach_obj. \
            _compare_total_file_size_to_threshold(self.example_contents, con_total_size)
        self.assertEqual((expected, expected_count, expected_tb), (returned, returned_count, returned_tb))

        # test the Exception case
        expected, expected_count = None, None
        rorschach_obj = Rorschach(event=self.example_event_daily, context=None)
        returned, returned_count, returned_tb = rorschach_obj. \
            _compare_total_file_size_to_threshold(None, con_total_size)
        self.assertEqual((expected, expected_count), (returned, returned_count))
        self.assertTrue(self.example_traceback in returned_tb)
