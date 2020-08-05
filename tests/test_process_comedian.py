import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.comedian import Comedian
from watchmen.process.comedian import MESSAGES, TARGET_EMAIL, TARGET_PAGER, GENERIC


class TestComedian(unittest.TestCase):

    def setUp(self):
        self.details = MESSAGES.get("success_details_single").format("OneTestyBoi")

        self.increment = 1
        self.threshold = 0.5

        self.quota_info_in_range = {'threshold_start': self.threshold * 100,
                                    'increment': self.increment,
                                    'quotas': {'ITSOVER9000': {'used': 1, 'allowed': 9000}}}

        self.quota_info_out_range = {'threshold_start': self.threshold * 100,
                                     'increment': self.increment,
                                     'quotas': {'ITSOVER9000': {'used': 9001, 'allowed': 9000}}}

        self.traceback = "Traceback created during exception catch."

        # Constant that use a previously declared constant.
        self.exceeded_quota_message = MESSAGES.get("quota_exceeded") \
            .format("ITSOVER9000", self.threshold * 100, 100.01, 9001, 9000)

        # Constants that use previously declared constants.
        self.check_err = {"OneTestyBoi": {
            "success": None,
            'api_details': "\n\nOneTestyBoi" + "\n" +
                           MESSAGES.get("exception_details").format("OneTestyBoi", self.traceback),
            'snapshot': self.quota_info_in_range
        }}

        self.check_results_in_range = {"OneTestyBoi": {
            'success': True,
            'api_details': "\n\nOneTestyBoi\n",
            'snapshot': self.quota_info_in_range
        }}

        self.check_results_out_range = {"OneTestyBoi": {
            'success': False,
            'api_details': "\n\nOneTestyBoi" + "\n" + self.exceeded_quota_message,
            'snapshot': self.quota_info_out_range
        }}

        self.config = [{'target_name': 'OneTestyBoi',
                        'timestamp': '%Y-%m-%dT%H:%M:%SZ',
                        'hash': 'sha1',
                        'encode': 'utf-8',
                        'threshold_start': self.threshold * 100,
                        'increment': self.increment,
                        'head': {'oogabooga': 'timestamp',
                                 'signature': {'tag': 'special_signature',
                                               'api_key': 'apikey',
                                               'msg': {'hello_there': 'general Kenobi'}}},
                        'url': 'www.www.com.org/API?timestamp={timestamp}&signature={signature}',
                        'url_arguments': {'timestamp': None,
                                          'signature': {'key': '12345',
                                                        'msg': {'hello_there': 'general Kenobi'}}}
                        }]

        self.config_entry = {'target_name': 'OneTestyBoi',
                             'timestamp': '%Y-%m-%dT%H:%M:%SZ',
                             'hash': 'sha1',
                             'encode': 'utf-8',
                             'threshold_start': self.threshold * 100,
                             'increment': self.increment,
                             'head': {'oogabooga': 'timestamp',
                                      'signature': {'tag': 'special_signature',
                                                    'api_key': 'apikey',
                                                    'msg': {'hello_there': 'general Kenobi'}},
                                      'x-api-key': 'apikey'},
                             'url': 'www.www.com.org/API?timestamp={timestamp}&signature={signature}',
                             'url_arguments': {'timestamp': None,
                                               'signature': {'api_key': 'apikey',
                                                             'msg': {'hello_there': 'general Kenobi'}}},
                             'quotas': ''
                             }

        self.failure_results = [{
            "details": "\n\nOneTestyBoi" + "\n" + self.exceeded_quota_message,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("failure_short_message_single").format('OneTestyBoi'),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": self.quota_info_out_range,
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject_single").format('OneTestyBoi'),
            "success": False,
            "target": TARGET_EMAIL.format('OneTestyBoi'),
        }, {
            "details": MESSAGES.get("failure_short_message_single").format('OneTestyBoi'),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("failure_short_message_single").format('OneTestyBoi'),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": self.quota_info_out_range,
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject_single").format('OneTestyBoi'),
            "success": False,
            "target": TARGET_PAGER.format('OneTestyBoi'),
        }, {
            "details": "\n\nOneTestyBoi" + "\n" + self.exceeded_quota_message + "\n" + const.MESSAGE_SEPARATOR,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("failure_short_message"),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": TARGET_EMAIL.format(GENERIC),
        }
        ]

        self.formatted_data = {
            'threshold_start': self.threshold * 100,
            'increment': self.increment,
            'quotas': {}}

        self.params_err = [{
            'details': self.traceback,
            'disable_notifier': False,
            'short_message': MESSAGES.get("exception_short_message"),
            'snapshot': {},
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_subject"),
            'success': False,
            'api_name': 'OneTestyBoi'}]

        self.params_succeed = [{
            'details': self.details,
            'disable_notifier': True,
            'short_message': MESSAGES.get("success_short_message_single").format('OneTestyBoi'),
            'snapshot': self.quota_info_in_range,
            'state': 'SUCCESS',
            'subject': MESSAGES.get("success_subject_single").format('OneTestyBoi'),
            'success': True,
            'api_name': 'OneTestyBoi'}]

        self.params_fail = [{
            'details': "\n\n" + "OneTestyBoi\n" + self.exceeded_quota_message,
            'disable_notifier': False,
            'short_message': MESSAGES.get("failure_short_message_single").format('OneTestyBoi'),
            'snapshot': self.quota_info_out_range,
            'state': 'FAILURE',
            'subject': MESSAGES.get("failure_subject_single").format('OneTestyBoi'),
            'success': False,
            'api_name': 'OneTestyBoi'}]

        self.successful_results = [{
            "details": MESSAGES.get("success_details_single").format('OneTestyBoi'),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message_single").format('OneTestyBoi'),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": self.quota_info_in_range,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject_single").format('OneTestyBoi'),
            "success": True,
            "target": TARGET_EMAIL.format('OneTestyBoi'),
        }, {
            "details": MESSAGES.get("success_short_message_single").format('OneTestyBoi'),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message_single").format('OneTestyBoi'),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": self.quota_info_in_range,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject_single").format('OneTestyBoi'),
            "success": True,
            "target": TARGET_PAGER.format('OneTestyBoi'),
        }, {
            "details": MESSAGES.get("success_details_single").format('OneTestyBoi') + "\n" + const.MESSAGE_SEPARATOR,
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_short_message"),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET_EMAIL.format(GENERIC),
        }]

    @staticmethod
    def _create_comedian_obj():
        """
        Creates a Comedian object.
        @return: <Comedian> object.
        """
        return Comedian(event=None, context=None)

    @patch("watchmen.process.comedian.Comedian._check_api_quotas")
    @patch("watchmen.process.comedian.Comedian._get_targets_quota_info")
    @patch("watchmen.process.comedian.Comedian._load_config")
    def test_monitor(self, mock_config, mock_api_status, mock_api_params):
        comedian_obj = self._create_comedian_obj()

        config_exception_results = [{
            "details": MESSAGES.get("exception_config_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_short_message"),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_EMAIL.format(GENERIC),
        }]
        api_quota_exception_result = [{
            "details": MESSAGES.get("exception_api_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_short_message"),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_EMAIL.format(GENERIC),
        }]

        api_check_exception_result = [{
            "details": MESSAGES.get("quota_exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_short_message"),
            "watchman_name": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_EMAIL.format(GENERIC),
        }]

        tests = [
            {
                "api_config": self.config,
                "quota_info": self.quota_info_in_range,
                "check_results": self.check_results_in_range,
                "config_tb": "",
                "quota_tb": "",
                "check_tb": "",
                "results": self.successful_results
            },
            {
                "api_config": self.config,
                "quota_info": self.quota_info_out_range,
                "check_results": self.check_results_out_range,
                "config_tb": "",
                "quota_tb": "",
                "check_tb": "",
                "results": self.failure_results
            },
            {
                "api_config": None,
                "quota_info": self.quota_info_in_range,
                "check_results": None,
                "config_tb": self.traceback,
                "quota_tb": "",
                "check_tb": "",
                "results": config_exception_results
            },
            {
                "api_config": self.config,
                "quota_info": None,
                "check_results": None,
                "config_tb": "",
                "quota_tb": self.traceback,
                "check_tb": "",
                "results": api_quota_exception_result
            },
            {
                "api_config": self.config,
                "quota_info": self.quota_info_out_range,
                "check_results": None,
                "config_tb": "",
                "quota_tb": "",
                "check_tb": self.traceback,
                "results": api_check_exception_result
            }
        ]

        for test in tests:
            mock_config.return_value = test.get("api_config"), test.get("config_tb")
            mock_api_status.return_value = test.get("quota_info")
            mock_api_params.return_value = test.get("check_results"), test.get("check_tb")

            expected_results = test.get("results")
            returned_results = comedian_obj.monitor()
            if len(returned_results) is 1 and len(expected_results) is 1:
                # if an exception occured
                returned_email_result = returned_results[0].to_dict()
                returned_email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
                self.assertEqual(expected_results[0], returned_email_result)
            else:
                returned_pager_result = returned_results[0].to_dict()
                returned_email_result = returned_results[1].to_dict()
                returned_generic_result = returned_results[2].to_dict()
                returned_pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
                returned_email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
                returned_generic_result["dt_created"] = "2018-12-18T00:00:00+00:00"
                self.assertEqual(expected_results[0], returned_pager_result)
                self.assertEqual(expected_results[1], returned_email_result)
                self.assertEqual(expected_results[2], returned_generic_result)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch("watchmen.process.comedian.Comedian._get_api_key")
    def test_build_header(self, mock_api_key, mock_traceback):
        comedian_obj = self._create_comedian_obj()
        timestamp = "2018-12-18T00:00:00+00:00"
        head_no_key = {
            'timestamp': '%Y-%m-%dT%H:%M:%SZ',
            'hash': 'sha1',
            'encode': 'utf-8',
            'head': {
                'wait-its-all-header': 'Always has been',
                'oogabooga': 'timestamp',
                'signature': {'tag': 'special_signature',
                              'key': 'IMFREEE',
                              'msg': {'hello_there': 'general Kenobi'}},
                'x-api-key': 'apikey'},
        }

        tests = [
            {
                "config": self.config_entry,
                "api_key": 'secretSHHHHH',
                "expected": {
                    'oogabooga': timestamp,
                    'special_signature': 'c313b3b901a912a60c6a4ca36362a15820d1ffe7',
                    'x-api-key': 'secretSHHHHH',
                },
                "tb": None
            },
            {
                "config": head_no_key,
                "api_key": 'secretSHHHHH',
                "expected": {
                    'wait-its-all-header': 'Always has been',
                    'oogabooga': timestamp,
                    'special_signature': '232cc7eaf9137ecc98bcb191571841a673f69156',
                    'x-api-key': 'secretSHHHHH',
                },
                "tb": None
            },
            {
                "config": None,
                "api_key": None,
                "expected": None,
                "tb": self.traceback
            }
        ]

        for test in tests:
            traceback = test.get("tb")
            mock_traceback.return_value = traceback
            mock_api_key.return_value = test.get("api_key")
            config = test.get("config")
            expected = test.get("expected")
            returned = comedian_obj._build_header(config, timestamp)
            self.assertEqual((expected, traceback), returned)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch("watchmen.process.comedian.Comedian._get_api_key")
    def test_build_url(self, mock_api_key, mock_traceback):
        comedian_obj = self._create_comedian_obj()
        timestamp = "2018-12-18T00:00:00+00:00"
        just_url = {'url': "www.www.com.org/API?timestamp={timestamp}&signature={signature}"}
        no_api_key = {
            'timestamp': '%Y-%m-%dT%H:%M:%SZ',
            'hash': 'sha1',
            'encode': 'utf-8',
            'url': 'www.www.com.org/API?timestamp={timestamp}&signature={signature}{random}',
            'url_arguments': {
                'timestamp': None,
                'signature': {
                    'key': 'IMFREEE',
                    'msg': {'hello_there': 'general Kenobi'}},
                'random': 'random'}}

        tests = [
            {
                "config": self.config_entry,
                "api_key": 'secretSHHHHH',
                "expected": 'www.www.com.org/'
                            'API?timestamp=2018-12-18T00:00:00+00:00'
                            '&signature=c313b3b901a912a60c6a4ca36362a15820d1ffe7',
                "tb": None
            },
            {
                "config": just_url,
                "api_key": None,
                "expected": "www.www.com.org/API?timestamp={timestamp}&signature={signature}",
                "tb": None
            },
            {
                "config": no_api_key,
                "api_key": 'secretSHHHHH',
                "expected": 'www.www.com.org/'
                            'API?timestamp=2018-12-18T00:00:00+00:00'
                            '&signature=232cc7eaf9137ecc98bcb191571841a673f69156random',
                "tb": None
            },
            {
                "config": None,
                "api_key": None,
                "expected": None,
                "tb": self.traceback
            }
        ]

        for test in tests:
            traceback = test.get("tb")
            mock_traceback.return_value = traceback
            mock_api_key.return_value = test.get("api_key")
            config = test.get("config")
            expected = test.get("expected")
            returned = comedian_obj._build_url(config, timestamp)
            self.assertEqual((expected, traceback), returned)

    @patch("watchmen.process.comedian.datetime")
    def test_calculate_threshold(self, mock_datetime):

        mock_datetime.utcnow.return_value = datetime(year=2019, month=12, day=15, tzinfo=pytz.utc)
        comedian_obj = self._create_comedian_obj()

        # (THRESHOLD_START + (15 * 1)) / 100 = 0.65
        tests = [
            {
                'config': self.config_entry,
                'threshold': 0.65
            },
            {
                'config': None,
                'threshold': None
            }
        ]

        for test in tests:
            expected_threshold = test.get('threshold')
            returned_threshold, tb = comedian_obj._calculate_threshold(test.get('config'))
            self.assertEqual(expected_threshold, returned_threshold)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch("watchmen.process.comedian.Comedian._calculate_threshold")
    def test_check_api_quotas(self, mock_threshold, mock_traceback):
        comedian_obj = self._create_comedian_obj()
        api_err = {'OneTestyBoi': self.traceback}
        api_in_range = {'OneTestyBoi': self.quota_info_in_range}
        api_out_range = {'OneTestyBoi': self.quota_info_out_range}
        api_used_none = {'OneTestyBoi': {'threshold_start': self.threshold * 100,
                                         'increment': self.increment,
                                         'quotas': {'ITSOVER9000': {'used': None, 'allowed': 9000}}}}
        api_strings = {'OneTestyBoi': {'threshold_start': self.threshold * 100,
                                       'increment': self.increment,
                                       'quotas': {'ITSOVER9000': {'used': "1", 'allowed': "9000"}}}}

        api_err_check = {"OneTestyBoi": {
                            'success': None,
                            'api_details': MESSAGES.get("exception_details").format('OneTestyBoi', self.traceback),
                            'snapshot': self.traceback}}

        used_api_none_check = {"OneTestyBoi": {
                                "success": None,
                                'api_details': "\n\nOneTestyBoi" + "\n" +
                                               MESSAGES.get("exception_quota_details").format("ITSOVER9000"),
                                'snapshot': api_used_none.get("OneTestyBoi")
                                }}

        strings_check = {"OneTestyBoi": {
            "success": True,
            'api_details': "\n\nOneTestyBoi" + "\n",
            'snapshot': api_strings.get("OneTestyBoi")
        }}

        tests = [
            {
                "api_info": api_out_range,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": self.check_results_out_range,
                "tb": None
            },
            {
                "api_info": api_in_range,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": self.check_results_in_range,
                "tb": None
            },
            {
                "api_info": api_in_range,
                "threshold": None,
                "threshold_tb": self.traceback,
                "result": self.check_err,
                "tb": None
            },
            {
                "api_info": api_used_none,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": used_api_none_check,
                "tb": None
            },
            {
                "api_info": None,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": None,
                "tb": self.traceback
            },
            {
                "api_info": api_strings,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": strings_check,
                "tb": None
            },
            {
                "api_info": api_err,
                "threshold": self.threshold,
                "threshold_tb": None,
                "result": api_err_check,
                "tb": None
            }
        ]

        for test in tests:
            api_info = test.get("api_info")
            expected = test.get("result"), test.get("tb")
            mock_threshold.return_value = test.get("threshold"), test.get("threshold_tb")
            mock_traceback.return_value = self.traceback
            returned = comedian_obj._check_api_quotas(api_info)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.traceback.format_exc')
    def test_create_data_template(self, mock_traceback):
        comedian_obj = self._create_comedian_obj()

        tests = [
            {
                "config": self.config_entry,
                "expected": self.formatted_data,
                "tb": None
            },
            {
                "config": None,
                "expected": None,
                "tb": self.traceback
            }
        ]

        for test in tests:
            mock_traceback.return_value = test.get("tb")
            expected = (test.get("expected"), test.get("tb"))
            returned = comedian_obj._create_data_template(test.get("config"))
            self.assertEqual(expected, returned)

    def test_create_results(self):
        comedian_obj = self._create_comedian_obj()

        tests = [
            {
                "params": self.params_succeed,
                "expected": self.successful_results,
                "failure": False,
                "exception": False
            },
            {
                "params": self.params_fail,
                "expected": self.failure_results,
                "failure": True,
                "exception": False
            },
        ]

        for test in tests:
            expected = test.get("expected")
            returned = comedian_obj._create_results(test.get("params"), test.get("failure"), test.get("exception"))

            returned_pager_result = returned[0].to_dict()
            returned_email_result = returned[1].to_dict()
            returned_generic_result = returned[2].to_dict()

            returned_pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_generic_result["dt_created"] = "2018-12-18T00:00:00+00:00"

            self.assertEqual(expected[0], returned_pager_result)
            self.assertEqual(expected[1], returned_email_result)
            self.assertEqual(expected[2], returned_generic_result)

    def test_create_result_parameters(self):
        comedian_obj = self._create_comedian_obj()

        param_err = [{
            'details': "\n\nOneTestyBoi" + "\n" +
                       MESSAGES.get("exception_details").format("OneTestyBoi", self.traceback),
            'disable_notifier': False,
            'short_message': MESSAGES.get("exception_short_message"),
            'snapshot': self.quota_info_in_range,
            'state': 'EXCEPTION',
            'subject': MESSAGES.get("exception_subject"),
            'success': False,
            'api_name': 'OneTestyBoi'}]

        tests = [
            {
                "check": self.check_results_in_range,
                "expected": (self.params_succeed, False, False)
            },
            {
                "check": self.check_results_out_range,
                "expected": (self.params_fail, True, False)
            },
            {
                "check": self.check_err,
                "expected": (param_err, False, True)
            }
        ]

        for test in tests:
            expected = test.get("expected")
            returned = comedian_obj._create_result_parameters(test.get("check"))
            self.assertEqual(expected, returned)

    def test_create_sign(self):
        comedian_obj = self._create_comedian_obj()
        msg_basic = {'hello_there': 'general Kenobi'}
        msg_timestamp = {'hello_there': 'general Kenobi', 'timestamp': ''}
        timestamp = "2018-12-18T00:00:00+00:00"
        tests = [
            {
                'sign_key': 'IMFREEE',
                'msg': msg_basic,
                'timestamp': None,
                'hash_alg': 'sha1',
                'encode': 'utf-8',
                'expected': '232cc7eaf9137ecc98bcb191571841a673f69156'
            },
            {
                'sign_key': 'IMFREEE',
                'msg': msg_timestamp,
                'timestamp': timestamp,
                'hash_alg': 'sha1',
                'encode': 'utf-8',
                'expected': '8c0414125ac68cfa67ff49c2baeeb176d94ad132'
            },
            {
                'sign_key': 'IMFREEE',
                'msg': msg_basic,
                'timestamp': None,
                'hash_alg': 'sha256',
                'encode': 'utf-8',
                'expected': 'b24f811928aeeec0ac670eda5fbb5471ea10c0b17bbf7a675932980f38ff568a'
            },
            {
                'sign_key': 'IMFREEE',
                'msg': msg_basic,
                'timestamp': None,
                'hash_alg': None,
                'encode': 'utf-8',
                'expected': None
            }
        ]

        for test in tests:
            sign_key = test.get("sign_key")
            msg = test.get("msg")
            timestamp = test.get("timestamp")
            hash_alg = test.get("hash_alg")
            encode = test.get("encode")
            expected = test.get("expected")
            returned = comedian_obj._create_signature(sign_key, msg, timestamp, hash_alg, encode)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch('watchmen.process.comedian.getattr')
    def test_get_api_info(self, mock_att, mock_traceback):
        comedian_obj = self._create_comedian_obj()

        tests = [
            {
                "method": lambda api: (self.quota_info_in_range, None),
                "expected": self.quota_info_in_range,
                "tb": None,
            },
            {
                "method": Exception(),
                "expected": None,
                "tb": self.traceback,
            }
        ]

        for test in tests:
            mock_att.return_value = test.get("method")
            mock_traceback.return_value = test.get("tb")
            returned = comedian_obj._get_api_info(self.config_entry)
            expected = test.get("expected"), test.get('tb')
            self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.settings')
    def test_get_api_key(self, mock_settings):
        comedian_obj = self._create_comedian_obj()
        expected = '123456'
        mock_settings.return_value = '123456'
        returned = comedian_obj._get_api_key(self.config_entry)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch("watchmen.process.comedian.Comedian._get_api_info")
    def test_get_targets_quota_info(self, mock_api_info, mock_traceback):
        comedian_obj = self._create_comedian_obj()
        result_good = {'OneTestyBoi': self.quota_info_in_range}
        result_bad = {'OneTestyBoi': self.traceback}
        result_err = {"ERROR": self.traceback}
        bad_config = [{
                        'timestamp': '%Y-%m-%dT%H:%M:%SZ',
                        }]

        tests = [
            {
                'api_config': self.config,
                'quota_info': self.quota_info_in_range,
                'tb': None,
                'result': result_good
            },
            {
                'api_config': self.config,
                'quota_info': None,
                'tb': self.traceback,
                'result': result_bad
            },
            {
                'api_config': bad_config,
                'quota_info': None,
                'tb': self.traceback,
                'result': result_err
            }
        ]
        for test in tests:
            mock_traceback.return_value = test.get("tb")
            mock_api_info.return_value = test.get("quota_info"), test.get("tb")
            returned = comedian_obj._get_targets_quota_info(test.get("api_config"))
            self.assertEqual(test.get("result"), returned)

    @patch('watchmen.process.comedian.Comedian._create_data_template')
    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch('watchmen.process.comedian.requests.get')
    @patch('watchmen.process.comedian.Comedian._build_url')
    def test_get_domaintools_data(self, mock_url, mock_get_request, mock_traceback, mock_data_temp):
        comedian_obj = self._create_comedian_obj()

        api_response = {'response': {'products': [{'id': 'api_requests_monthly',
                                                   'usage': {'month': '1'},
                                                   'per_month_limit': '9000'}]}}
        config_quotas = {'target_name': 'OneTestyBoi',
                         'timestamp': '%Y-%m-%dT%H:%M:%SZ',
                         'threshold_start': self.threshold * 100,
                         'increment': self.increment,
                         "quotas": ['api_requests_monthly']}

        formatted_test_data = {
            'threshold_start': self.threshold * 100,
            'increment': self.increment,
            'quotas': {'api_requests_monthly': {'used': '1', 'allowed': '9000'}}}

        tests = [
            {
                'request': api_response,
                'config': config_quotas,
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (self.formatted_data, None),
                'expected': (formatted_test_data, None)
            },
            {
                'request': api_response,
                'config': config_quotas,
                'url': (None, self.traceback),
                'formatted data': (self.formatted_data, None),
                'expected': (None, self.traceback)
            },
            {
                'request': api_response,
                'config': config_quotas,
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (None, self.traceback),
                'expected': (None, self.traceback)
            },
            {
                'request': None,
                'config': config_quotas,
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (None, self.traceback),
                'expected': (None, self.traceback)
            }
        ]

        for test in tests:
            mock_traceback.return_value = self.traceback
            mock_data_temp.return_value = test.get("formatted data")
            mock_url.return_value = test.get("url")
            mock_get_request.return_value.json.return_value = test.get("request")
            expected = test.get("expected")
            returned = comedian_obj._get_domaintools_data(test.get("config"))
            self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.Comedian._create_data_template')
    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch('watchmen.process.comedian.requests.get')
    @patch('watchmen.process.comedian.Comedian._build_url')
    @patch('watchmen.process.comedian.Comedian._build_header')
    def test_get_virustotal_data(self, mock_header, mock_url, mock_get_request, mock_traceback, mock_data_temp):
        comedian_obj = self._create_comedian_obj()

        api_response = {
            'data': {'attributes': {'quotas': {'api_requests_monthly': {'allowed': 1000000000, 'used': 1004}}}}}
        config_quotas = {'target_name': 'OneTestyBoi',
                         'threshold_start': self.threshold * 100,
                         'increment': self.increment,
                         "quotas": ['api_requests_monthly']}

        formatted_test_data = {
            'threshold_start': self.threshold * 100,
            'increment': self.increment,
            'quotas': {'api_requests_monthly': {'used': 1004, 'allowed': 1000000000}}}

        tests = [
            {
                'request': api_response,
                'config': config_quotas,
                'header': ({"head": "head"}, None),
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (self.formatted_data, None),
                'expected': (formatted_test_data, None)
            },
            {
                'request': api_response,
                'config': config_quotas,
                'header': (None, self.traceback),
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (self.formatted_data, None),
                'expected': (None, self.traceback)
            },
            {
                'request': api_response,
                'config': config_quotas,
                'header': ({"head": "head"}, None),
                'url': (None, self.traceback),
                'formatted data': (self.formatted_data, None),
                'expected': (None, self.traceback)
            },
            {
                'request': api_response,
                'config': config_quotas,
                'header': ({"head": "head"}, None),
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (None, self.traceback),
                'expected': (None, self.traceback)
            },
            {
                'request': None,
                'config': config_quotas,
                'header': ({"head": "head"}, None),
                'url': ('www.superepicwebsite.com', None),
                'formatted data': (None, self.traceback),
                'expected': (None, self.traceback)
            }
        ]

        for test in tests:
            mock_traceback.return_value = self.traceback
            mock_data_temp.return_value = test.get("formatted data")
            mock_header.return_value = test.get("header")
            mock_url.return_value = test.get("url")
            mock_get_request.return_value.json.return_value = test.get("request")
            expected = test.get("expected")
            returned = comedian_obj._get_virustotal_data(test.get("config"))
            self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.traceback.format_exc')
    @patch('watchmen.process.comedian.yaml.load')
    @patch('watchmen.process.comedian.open')
    def test_load_config(self, mock_open, mock_yaml_read, mock_traceback):
        comedian_obj = self._create_comedian_obj()

        tests = [
            {
                'open': True,
                'config': self.config,
                'tb': None,
                'expected': self.config
            },
            {
                'open': False,
                'config': Exception(),
                'tb': self.traceback,
                'expected': None
            }
        ]

        for test in tests:
            if not test.get("open"):
                mock_open.return_value = Exception()
            mock_yaml_read.return_value = test.get("config")
            mock_traceback.return_value = test.get("tb")
            expected = test.get("expected"), test.get("tb")
            returned = comedian_obj._load_config()
            self.assertEqual(expected, returned)
