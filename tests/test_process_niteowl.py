import datetime
import unittest
from mock import mock_open, patch

from watchmen.process.niteowl import Niteowl, MESSAGES, REQUIRED_TARGET_TAGS, GENERIC_TARGET, const


class TestNiteowl(unittest.TestCase):
    def setUp(self):
        self.daily_event = {"Type": "Daily"}
        self.target_name = 'testy one'
        self.traceback = 'traceback'
        self.change = 'failure'
        self.success_details = MESSAGES.get('success_details').format(self.target_name)
        self.exception_details = MESSAGES.get('exception_details').format(self.target_name, self.traceback) + '\n\n'
        self.change_detected_details = \
            MESSAGES.get('change_detected_details').format(self.target_name, self.change) + '\n\n'
        self.change_w_exception_generic_details = \
            self.exception_details + const.MESSAGE_SEPARATOR + "\n\n" + self.change_detected_details

        self.config_not_loaded_result = {
            'details': MESSAGES.get('exception_config_load_failure_details'),
            'snapshot': {},
            'disable_notifier': False,
            'short_message': MESSAGES.get('exception_message'),
            'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
            'result_id': 0,
            'success': False,
            'watchman_name': 'Niteowl',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get('exception_config_load_failure_subject'),
            'target': GENERIC_TARGET
        }

        self.example_commits = [
            {
                'sha': 'e19957af106999e8048679c08df39bc2b71bee98',
                'commit': {'author': {'name': 'Isabel Tuson', 'email': 'isabel@mitre.org',
                                      'date': '2021-02-24T18:12:58Z'},
                           'message': 'fix usage table'},
                'html_url': 'https://github.com/mitre/cti/commit/e19957af106999e8048679c08df39bc2b71bee98'}
        ]

        self.example_config_file = {
            "Daily":
                [{
                    'target_name': self.target_name,
                    'owner': 'testy',
                    'repo': 'one',
                    'checks': ['Commits', 'Releases'],
                    'time_offset': 1}]
        }

        self.example_target = [{
            'target_name': self.target_name,
            'owner': 'testy',
            'repo': 'one',
            'checks': ['Commits'],
            'time_offset': 1
        }]

        self.new_change_string = [
            'New Commit:\n'
            'Date:2021-02-24T18:12:58Z\n'
            'SHA:e19957af106999e8048679c08df39bc2b71bee98\n'
            'Message:fix usage table\n'
            'Url:https://github.com/mitre/cti/commit/e19957af106999e8048679c08df39bc2b71bee98\n']

        self.invalid_event_result = {
            'details': MESSAGES.get('exception_invalid_event_details'),
            'snapshot': {},
            'disable_notifier': False,
            'short_message': MESSAGES.get('exception_message'),
            'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
            'result_id': 0,
            'success': False,
            'watchman_name': 'Niteowl',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get('exception_invalid_event_subject'),
            'target': GENERIC_TARGET
        }

        self.processed_targets_exception = [
            {
                'target_name': self.target_name,
                'success': None,
                'exception_strings': [self.traceback],
                'new_changes_strings': []
            }
        ]
        self.processed_targets_new_change = [
            {
                'target_name': self.target_name,
                'success': False,
                'exception_strings': [],
                'new_changes_strings': [self.change]
            }
        ]
        self.processed_targets_success = [
            {
                'target_name': self.target_name,
                'success': True,
                'exception_strings': [],
                'new_changes_strings': []
            }
        ]

        self.results_exception = [
            {
                'details': self.exception_details,
                'snapshot': {},
                'disable_notifier': False,
                'short_message': MESSAGES.get('exception_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': False,
                'watchman_name': 'Niteowl',
                'state': 'EXCEPTION',
                'subject': MESSAGES.get('exception_subject').format(self.target_name),
                'target': self.target_name
            },
            {
                'details': self.exception_details + const.MESSAGE_SEPARATOR + '\n\n',
                'snapshot': {},
                'disable_notifier': False,
                'short_message': MESSAGES.get('exception_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': False,
                'watchman_name': 'Niteowl',
                'state': 'EXCEPTION',
                'subject': MESSAGES.get("generic_exception_subject"),
                'target': GENERIC_TARGET
            }
        ]
        self.results_new_change = [
            {
                'details': self.change_detected_details,
                'snapshot': {},
                'disable_notifier': False,
                'short_message': MESSAGES.get('change_detected_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': False,
                'watchman_name': 'Niteowl',
                'state': 'FAILURE',
                'subject': MESSAGES.get('change_detected_subject').format(self.target_name),
                'target': self.target_name
            },
            {
                'details': self.change_detected_details + const.MESSAGE_SEPARATOR + '\n\n',
                'snapshot': {},
                'disable_notifier': False,
                'short_message': MESSAGES.get('change_detected_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': False,
                'watchman_name': 'Niteowl',
                'state': 'FAILURE',
                'subject': MESSAGES.get("generic_change_detected_subject"),
                'target': GENERIC_TARGET
            }
        ]
        self.results_success = [
            {
                'details': MESSAGES.get('success_details').format(self.target_name),
                'snapshot': {},
                'disable_notifier': True,
                'short_message': MESSAGES.get('success_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': True,
                'watchman_name': 'Niteowl',
                'state': 'SUCCESS',
                'subject': MESSAGES.get('success_subject').format(self.target_name),
                'target': self.target_name
            },
            {
                'details': '',
                'snapshot': {},
                'disable_notifier': True,
                'short_message': MESSAGES.get('success_message'),
                'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
                'result_id': 0,
                'success': True,
                'watchman_name': 'Niteowl',
                'state': 'SUCCESS',
                'subject': MESSAGES.get('generic_success_subject'),
                'target': GENERIC_TARGET
            }
        ]

        self.summary_parameter_exception = [
            {
                'disable_notifier': False,
                'state': 'EXCEPTION',
                'success': None,
                'target': self.target_name,
                'details': self.exception_details,
                'short_message': MESSAGES.get('exception_message'),
                'subject': MESSAGES.get('exception_subject').format(self.target_name)
            }
        ]
        self.summary_parameter_new_change = [
            {
                'disable_notifier': False,
                'state': 'FAILURE',
                'success': False,
                'target': self.target_name,
                'details': self.change_detected_details,
                'short_message': MESSAGES.get('change_detected_message'),
                'subject': MESSAGES.get('change_detected_subject').format(self.target_name)
            }
        ]
        self.summary_parameter_success = [
            {
                'disable_notifier': True,
                'state': 'SUCCESS',
                'success': True,
                'target': self.target_name,
                'details': MESSAGES.get('success_details').format(self.target_name),
                'short_message': MESSAGES.get('success_message'),
                'subject': MESSAGES.get('success_subject').format(self.target_name)
            }
        ]

    def _create_niteowl(self):
        """
        Create a Niteowl object with a Daily event.
        @return: <Niteowl> niteowl object
        """
        return Niteowl(context=None, event=self.daily_event)

    @patch('watchmen.process.niteowl.Niteowl._is_valid_event')
    @patch('watchmen.process.niteowl.Niteowl._create_invalid_event_result')
    @patch('watchmen.process.niteowl.Niteowl._load_config')
    @patch('watchmen.process.niteowl.Niteowl._create_config_not_loaded_result')
    @patch('watchmen.process.niteowl.Niteowl._process_targets')
    @patch('watchmen.process.niteowl.Niteowl._create_summary_parameters')
    @patch('watchmen.process.niteowl.Niteowl._create_results')
    def test_montior(self, mock_results, mock_summary, mock_targets, mock_config_res,
                     mock_config, mock_invalid_event, mock_event):
        """
        test watchmen.process.niteowl :: Niteowl :: monitor
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'valid_event': True,
                'load_config': (self.example_config_file.get('Daily'), None),
                'process_target': self.processed_targets_success,
                'summary_param': self.summary_parameter_success,
                'create_results': self.results_success,
                'expected': self.results_success
            },
            {
                'valid_event': False,
                'invalid_event_result': self.invalid_event_result,
                'load_config': (self.example_config_file.get('Daily'), None),
                'process_target': None,
                'summary_param': None,
                'create_results': None,
                'expected': self.invalid_event_result
            },
            {
                'valid_event': True,
                'load_config': (None, self.traceback),
                'invalid_config_result': self.config_not_loaded_result,
                'process_target': None,
                'summary_param': None,
                'create_results': None,
                'expected': self.config_not_loaded_result
            }
        ]

        for test in tests:
            mock_event.return_value = test.get('valid_event')
            mock_config.return_value = test.get('load_config')
            config, tb = test.get('load_config')
            if tb:
                mock_config_res.return_value = test.get('invalid_config_result')
            mock_targets.return_value = test.get('process_target')
            mock_summary.return_value = test.get('summary_param')
            mock_results.return_value = test.get('create_results')
            if not test.get('valid_event'):
                mock_invalid_event.return_value = test.get('invalid_event_result')

            result = niteowl.monitor()
            expected = test.get('expected')
            self.assertEqual(expected, result)

    def test_calculate_since_date(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _calculate_since_date
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'offset_type': 'Daily',
                'time_offset': 1,
                'expected': (datetime.datetime.utcnow() - datetime.timedelta(days=1)).replace(microsecond=0)
            },
        ]

        for test in tests:
            result = niteowl._calculate_since_date(test.get('time_offset'), test.get('offset_type'))
            self.assertEqual(test.get('expected'), result)

    @patch('watchmen.process.niteowl.Niteowl._get_new_commits')
    def test_check_commits(self, mock_commits):
        """
        test watchmen.process.niteowl :: Niteowl :: _check_commits
        """
        example_target_w_path = {
            'target_name': self.target_name,
            'owner': 'testy',
            'repo': 'one',
            'checks': ['Commits', 'Releases'],
            'time_offset': 1,
            'target_path': ['/']
        }

        niteowl = self._create_niteowl()
        tests = [
            {
                "target": self.example_target[0],
                "commits": (self.new_change_string, []),
                "expected": (self.new_change_string, [])
            },
            {
                "target": self.example_target[0],
                "commits": ([], [MESSAGES.get("exception_api_failed")
                            .format('commits', self.target_name, self.traceback)]),
                "expected": ([],
                             [MESSAGES.get("exception_api_failed").format('commits', self.target_name, self.traceback)])
            },
            {
                "target": example_target_w_path,
                "commits": (self.new_change_string, []),
                "expected": (self.new_change_string, [])
            },
            {
                "target": example_target_w_path,
                "commits": (self.new_change_string, [MESSAGES.get("exception_api_failed_w_path")
                                                     .format('commits', self.target_name, '/', self.traceback)]),
                "expected": (self.new_change_string, [MESSAGES.get("exception_api_failed_w_path")
                             .format('commits', self.target_name, '/', self.traceback)])
            }
        ]
        for test in tests:
            mock_commits.return_value = test.get('commits')
            result = niteowl._check_commits(test.get('target'))
            self.assertEqual(test.get('expected'), result)

    @patch('watchmen.process.niteowl.github.get_repository_release')
    def test_check_releases(self, mock_releases):
        """
        test watchmen.process.niteowl :: Niteowl :: _check_releases
        """
        niteowl = self._create_niteowl()
        date = (datetime.datetime.utcnow() -
                datetime.timedelta(minutes=30)).replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

        release_no_update = {
            'url': 'https://api.github.com/repos/mitre/cti/releases/36978713',
            'name': 'ATT&CK version 8.2',
            'published_at': (datetime.datetime.utcnow() -
                             datetime.timedelta(days=2)).replace(microsecond=0).isoformat() + 'Z'}
        release_update = {
            'url': 'https://api.github.com/repos/mitre/cti/releases/36978713',
            'name': 'ATT&CK version 8.2',
            'published_at': (datetime.datetime.utcnow() -
                             datetime.timedelta(minutes=30)).replace(microsecond=0).isoformat() + 'Z'}

        tests = [
            {
                'target': self.example_target[0],
                'release': release_update,
                'traceback': None,
                'expected': (['New Release: \nName:ATT&CK version 8.2\n'
                              f' Release Date:{date}\n'
                              ' Url:https://api.github.com/repos/mitre/cti/releases/36978713\n'], [])
            },
            {
                'target': self.example_target[0],
                'release': release_no_update,
                'traceback': None,
                'expected': ([], [])
            },
            {
                'target': self.example_target[0],
                'release': release_no_update,
                'traceback': self.traceback,
                'expected': ([], [MESSAGES.get('exception_api_failed')
                             .format('releases', self.target_name, self.traceback)])
            },
        ]
        for test in tests:
            mock_releases.return_value = test.get('release'), test.get('traceback')
            result = niteowl._check_releases(test.get('target'))
            self.assertEqual(test.get('expected'), result)

    def test_create_config_not_loaded_result(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_config_not_loaded_result
        """
        niteowl = self._create_niteowl()
        expected = self.config_not_loaded_result
        result = niteowl._create_config_not_loaded_result()[0].to_dict()
        result['dt_created'] = datetime.datetime.utcnow().replace(microsecond=0)
        self.assertEqual(result, expected)

    def test_create_details(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_details
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'targets': self.processed_targets_success[0],
                'expected': self.success_details
            },
            {
                'targets': self.processed_targets_new_change[0],
                'expected': self.change_detected_details
            },
            {
                'targets': self.processed_targets_exception[0],
                'expected': self.exception_details
            }
        ]
        for test in tests:
            returned = niteowl._create_details(test.get('targets'))
            self.assertEqual(test.get('expected'), returned)

    def test_create_invalid_event_result(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_invalid_event_result
        """
        niteowl = self._create_niteowl()
        expected = self.invalid_event_result
        result = niteowl._create_invalid_event_result()[0].to_dict()
        result['dt_created'] = datetime.datetime.utcnow().replace(microsecond=0)
        self.assertEqual(result, expected)

    def test_create_results(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_results
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'parameter': self.summary_parameter_success,
                'expected': self.results_success
            },
            {
                'parameter': self.summary_parameter_new_change,
                'expected': self.results_new_change
            },
            {
                'parameter': self.summary_parameter_exception,
                'expected': self.results_exception
            },
        ]
        for test in tests:
            result = niteowl._create_results(test.get('parameter'))
            dict_results = []
            for obj in result:
                dict_result = obj.to_dict()
                dict_result['dt_created'] = datetime.datetime.utcnow().replace(microsecond=0)
                dict_results.append(dict_result)

            self.assertEqual(test.get('expected'), dict_results)

    def test_create_generic_result(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_generic_result
        """

        results_generic_exception_new_change = {
            'details': self.exception_details + const.MESSAGE_SEPARATOR + '\n\n' + self.change_detected_details,
            'snapshot': {},
            'disable_notifier': False,
            'short_message': MESSAGES.get("change_detected_exception_message"),
            'dt_created': datetime.datetime.utcnow().replace(microsecond=0),
            'result_id': 0,
            'success': False,
            'watchman_name': 'Niteowl',
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("generic_change_detected_exception_subject"),
            'target': GENERIC_TARGET
        }

        niteowl = self._create_niteowl()
        tests = [
            {
                "change_detected": False,
                "exception": False,
                "details": '',
                "expected": self.results_success[1]
            },
            {
                "change_detected": True,
                "exception": False,
                "details": self.change_detected_details + const.MESSAGE_SEPARATOR + '\n\n',
                "expected": self.results_new_change[1]
            },
            {
                "change_detected": False,
                "exception": True,
                "details": self.exception_details + const.MESSAGE_SEPARATOR + '\n\n',
                "expected": self.results_exception[1]
            },
            {
                "change_detected": True,
                "exception": True,
                "details": self.change_w_exception_generic_details,
                "expected": results_generic_exception_new_change
            }
        ]
        for test in tests:
            result = niteowl._create_generic_result(
                test.get('change_detected'),
                test.get('exception'),
                test.get('details')).to_dict()
            result['dt_created'] = datetime.datetime.utcnow().replace(microsecond=0)

            self.assertEqual(test.get('expected'), result)

    def test_create_summary_parameters(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _create_summary_parameters
        """
        processed_targets_exception_w_change = [
            {
                'target_name': self.target_name,
                'success': False,
                'exception_strings': [self.traceback],
                'new_changes_strings': [self.change]
            }
        ]

        summary_parameter_exception_w_change = [
            {
                'disable_notifier': False,
                'state': 'FAILURE',
                'success': False,
                'target': self.target_name,
                'details': self.exception_details + self.change_detected_details,
                'short_message': MESSAGES.get('change_detected_exception_message'),
                'subject': MESSAGES.get('change_detected_exception_subject').format(self.target_name)
            }
        ]

        niteowl = self._create_niteowl()
        tests = [
            {
                'processed_target': self.processed_targets_success,
                'expected': self.summary_parameter_success
            },
            {
                'processed_target': self.processed_targets_new_change,
                'expected': self.summary_parameter_new_change
            },
            {
                'processed_target': self.processed_targets_exception,
                'expected': self.summary_parameter_exception
            },
            {
                'processed_target': processed_targets_exception_w_change,
                'expected': summary_parameter_exception_w_change
            }
        ]

        for test in tests:
            result = niteowl._create_summary_parameters(test.get('processed_target'))
            self.assertEqual(test.get('expected'), result)

    def test_format_api_exceptions(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _format_api_exceptions
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'check_name': 'commits',
                'target_name': 'one testy',
                'tb': self.traceback,
                'path': None,
                'expected': MESSAGES.get("exception_api_failed").format('commits', 'one testy', self.traceback)
            },
            {
                'check_name': 'commits',
                'target_name': 'one testy',
                'tb': self.traceback,
                'path': '\\path\\',
                'expected': MESSAGES.get("exception_api_failed_w_path").format('commits', 'one testy', '\\path\\',
                                                                               self.traceback)
            }
        ]

        for test in tests:
            result = niteowl._format_api_exception(test.get('check_name'), test.get('target_name'), test.get('tb'),
                                                   test.get('path'))
            expected = test.get('expected')
            self.assertEqual(result, expected)

    def test_format_commits(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _format_commits
        """
        niteowl = self._create_niteowl()
        self.assertEqual(self.new_change_string, niteowl._format_commits(self.example_commits))

    @patch('watchmen.process.niteowl.github.get_repository_commits')
    def test_get_new_commits(self, mock_commits):
        """
        test watchmen.process.niteowl :: Niteowl :: _get_repo_commits
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'commits': self.example_commits,
                'tb': None,
                'formatted': (self.new_change_string, []),
                'paths': ['/']
            },
            {
                'commits': None,
                'tb': self.traceback,
                'formatted': ([], [MESSAGES.get('exception_api_failed').format(
                    'commits', self.target_name, self.traceback)]),
                'paths': [None]
            }
        ]
        for test in tests:
            mock_commits.return_value = (test.get('commits'), test.get('tb'))
            expected = test.get('formatted')
            result = niteowl._get_new_commits(self.target_name, 'test', 'test', 'date', test.get('paths'))
            self.assertEqual(expected, result)

    def test_is_valid_event(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _is_valid_event
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                'event': 'Daily',
                'expected': True
            },
            {
                'event': 'Dail',
                'expected': False
            }
        ]
        for test in tests:
            niteowl.event = test.get('event')
            self.assertEqual(test.get('expected'), niteowl._is_valid_event())

    @patch('builtins.open', new_callable=mock_open())
    @patch('watchmen.process.niteowl.yaml.load')
    @patch('watchmen.process.niteowl.traceback.format_exc')
    def test_load_config(self, mock_traceback, mock_file, mock_open):
        """
        test watchmen.process.niteowl :: Niteowl :: _load_config
        """
        tests = [
            {
                'config': self.example_config_file,
                'tb': None,
                'expected': self.example_config_file['Daily']
            },
            {
                'config': None,
                'tb': self.traceback,
                'expected': None
            }
        ]
        for test in tests:
            with mock_open:
                niteowl = self._create_niteowl()
                mock_file.return_value = test.get('config')
                mock_file.side_effect = Exception() if test.get('tb') else None
                mock_traceback.return_value = test.get('tb')
                result = niteowl._load_config()
                expected = (test.get('expected'), test.get('tb'))
                self.assertEqual(expected, result)

    @patch('watchmen.process.niteowl.Niteowl._validate_target_entry')
    @patch('watchmen.process.niteowl.Niteowl._run_check')
    def test_process_targets(self, mock_check, mock_valid_target):
        """
        test watchmen.process.niteowl :: Niteowl :: _process_targets
        """
        niteowl = self._create_niteowl()
        missing_tags = MESSAGES.get('exception_invalid_target_format').format(REQUIRED_TARGET_TAGS)
        exception_with_missing_tag = [{
            'target_name': self.target_name,
            'success': None,
            'exception_strings': [missing_tags],
            'new_changes_strings': []}]

        tests = [
            {
                'target': self.example_target,
                'is_valid_target': (True, ''),
                'new_changes_strings': [],
                'exception_strings': [],
                'expected': self.processed_targets_success
            },
            {
                'target': self.example_target,
                'is_valid_target': (True, ''),
                'new_changes_strings': [self.change],
                'exception_strings': [],
                'expected': self.processed_targets_new_change
            },
            {
                'target': self.example_target,
                'is_valid_target': (True, ''),
                'new_changes_strings': [],
                'exception_strings': [self.traceback],
                'expected': self.processed_targets_exception
            },
            {
                'target': self.example_target,
                'is_valid_target': (False, missing_tags),
                'new_changes_strings': [],
                'exception_strings': [missing_tags],
                'expected': exception_with_missing_tag
            }
        ]

        for test in tests:
            mock_check.return_value = test.get('new_changes_strings'), test.get('exception_strings')
            mock_valid_target.return_value = test.get('is_valid_target')
            result = niteowl._process_targets(test.get('target'))
            self.assertEqual(test.get('expected'), result)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch('watchmen.process.niteowl.getattr')
    def test_run_check(self, mock_att, mock_trace):
        """
        test watchmen.process.niteowl :: Niteowl :: _run_check
        """
        niteowl = self._create_niteowl()

        tests = [
            {
                'check_name': 'Commits',
                'target': self.example_target[0],
                "method": lambda check: ([], []),
                "tb": None,
                "expected": ([], []),
            },
            {
                'check_name': 'Commis',
                'target': self.example_target[0],
                "method": Exception(),
                "tb": self.traceback,
                "expected": ([], [MESSAGES.get('exception_invalid_check').format('Commis', self.target_name)]),
            }
        ]

        for test in tests:
            mock_att.return_value = test.get('method')
            mock_trace.return_value = test.get('tb')
            result = niteowl._run_check(test.get('check_name'), test.get('target'))
            self.assertEqual(test.get('expected'), result)

    def test_validate_target_entry(self):
        """
        test watchmen.process.niteowl :: Niteowl :: _validate_target_entry
        """
        niteowl = self._create_niteowl()
        tests = [
            {
                "target": self.example_target[0],
                "expected": (True, '')
            },
            {
                "target": {},
                "expected": (False, MESSAGES.get('exception_invalid_target_format').format(
                    REQUIRED_TARGET_TAGS))
            }
        ]
        for test in tests:
            result = niteowl._validate_target_entry(test.get('target'))
            self.assertEqual(test.get('expected'), result)
