import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.slater import Slater, MESSAGES, TARGET_EMAIL, TARGET_PAGER


class TestSlater(unittest.TestCase):
    def setUp(self):
        self.details = MESSAGES.get("success_details")
        self.in_range_quotas = [
            {'absolute_limit': None, 'expiration_date': '2021-02-02', 'id': 'domain-profile',
                'per_minute_limit': '120', 'per_month_limit': '10000', 'usage': {'month': '100', 'today': '0'}},
            {'absolute_limit': None, 'expiration_date': '2021-02-02', 'id': 'whois', 'per_minute_limit': '480',
                'per_month_limit': '1000000', 'usage': {'month': '0', 'today': '0'}},
            {'absolute_limit': None, 'expiration_date': '2021-02-02', 'id': 'whois-history',
                'per_minute_limit': '30', 'per_month_limit': '1000', 'usage': {'month': '1', 'today': '0'}}
        ]
        self.out_of_range_quotas = [
            {'absolute_limit': None, 'expiration_date': '2021-02-02', 'id': 'domain-profile',
                'per_minute_limit': '120', 'per_month_limit': '50', 'usage': {'month': '100', 'today': '0'}},
        ]
        self.threshold = 0.6
        self.traceback = "Traceback created during exception catch."

        # Constants that use previously declared constants.
        self.exceeded_quota_message = MESSAGES.get("quota_exceeded")\
                                              .format("domain-profile", self.threshold*100, 100, 50, 200.0) \
            + "\n" + const.MESSAGE_SEPARATOR + "\n"

        self.exception_parameters = [{
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_PAGER,
        }, {
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_EMAIL,
        },
        ]
        self.success_parameters = {
                "details": self.details,
                "disable_notifier": True,
                "short_message": MESSAGES.get("success_message"),
                "snapshot": self.in_range_quotas,
                "state": "SUCCESS",
                "subject": MESSAGES.get("success_subject"),
                "success": True,
        }
        self.successful_results = [{
            "details": MESSAGES.get("success_details"),
            "disable_notifier": True,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": self.in_range_quotas,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET_PAGER,
        }, {
            "details": MESSAGES.get("success_details"),
            "disable_notifier": True,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("success_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": self.in_range_quotas,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET_EMAIL,
        },
        ]

    @staticmethod
    def _create_slater_obj():
        """
        Creates a slater object.
        @return: <slater> object.
        """
        return Slater(event=None, context=None)

    @patch("watchmen.process.slater.Slater._calculate_threshold")
    @patch("watchmen.process.slater.Slater._get_quotas")
    def test_monitor(self, mock_response_info, mock_threshold):
        slater_obj = self._create_slater_obj()
        exception_results = [{
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_PAGER,
        }, {
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2020-04-18T00:00:00+00:00",
            "short_message": MESSAGES.get("exception_message"),
            "watchman_name": "Slater",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_EMAIL,
        },
        ]

        tests = [
            {
                "domaintool_quota_info": self.in_range_quotas,
                "tb": "",
                "results": self.successful_results
            },
            {
                "domaintool_quota_info": None,
                "tb": self.traceback,
                "results": exception_results
            }
        ]

        for test in tests:
            mock_response_info.return_value = test.get("domaintool_quota_info"), test.get("tb")
            mock_threshold.return_value = self.threshold
            expected_results = test.get("results")
            returned_results = slater_obj.monitor()

            returned_pager_result = returned_results[0].to_dict()
            returned_email_result = returned_results[1].to_dict()

            returned_pager_result["dt_created"] = "2020-04-18T00:00:00+00:00"

            returned_email_result["dt_created"] = "2020-04-18T00:00:00+00:00"

            self.assertEqual(expected_results[0], returned_pager_result)
            self.assertEqual(expected_results[1], returned_email_result)

    @patch("watchmen.process.slater.datetime")
    def test_calculate_threshold(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(year=2020, month=3, day=10, tzinfo=pytz.utc)
        slater_obj = self._create_slater_obj()

        # (THRESHOLD_START + (10 * 1)) / 100 = 0.60
        expected_threshold = 0.60
        returned_threshold = slater_obj._calculate_threshold()
        self.assertEqual(expected_threshold, returned_threshold)

    def test_check_quota(self):
        slater_obj = self._create_slater_obj()
        threshold = self.threshold

        tests = [
            {
                "quota": self.out_of_range_quotas,
                "success": False,
                "details": self.exceeded_quota_message
            },
            {
                "quota": self.in_range_quotas,
                "success": True,
                "details": ""
            }
        ]

        for test in tests:
            quota = test.get("quota")
            expected_success = test.get("success")
            expected_exceeded_quotas = test.get("details")
            returned = slater_obj._check_quota(threshold, quota)

            self.assertEqual(expected_success, returned.get("success"))
            self.assertEqual(expected_exceeded_quotas, returned.get("details"))

    def test_create_results(self):
        slater_obj = self._create_slater_obj()
        expected = self.successful_results
        returned = slater_obj._create_results(self.success_parameters)

        returned_pager_result = returned[0].to_dict()
        returned_email_result = returned[1].to_dict()

        returned_pager_result["dt_created"] = "2020-04-18T00:00:00+00:00"

        returned_email_result["dt_created"] = "2020-04-18T00:00:00+00:00"

        self.assertEqual(expected[0], returned_pager_result)
        self.assertEqual(expected[1], returned_email_result)

    def test_create_result_parameters(self):
        slater_obj = self._create_slater_obj()
        expected = self.success_parameters
        returned = slater_obj._create_result_parameters(True, self.details, self.in_range_quotas)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.slater.requests.get')
    @patch('watchmen.process.slater.traceback.format_exc')
    def test_get_quotas_exception(self, mock_traceback, mock_request):
        traceback = self.traceback
        mock_request.side_effect = Exception()
        mock_traceback.return_value = traceback
        slater_obj = self._create_slater_obj()

        expected = None, traceback
        returned = slater_obj._get_quotas()

        self.assertEqual(expected, returned)

    @patch('watchmen.process.slater.traceback.format_exc')
    def test_create_exception_results(self, mock_traceback):
        traceback = self.traceback
        slater_obj = self._create_slater_obj()

        expected = self.exception_parameters
        returned = slater_obj._create_exception_results(traceback)

        returned_pager_result = returned[0].to_dict()
        returned_email_result = returned[1].to_dict()

        returned_pager_result["dt_created"] = "2020-04-18T00:00:00+00:00"

        returned_email_result["dt_created"] = "2020-04-18T00:00:00+00:00"

        self.assertEqual(expected[0], returned_pager_result)
        self.assertEqual(expected[1], returned_email_result)
