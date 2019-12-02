import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.comedian import Comedian
from watchmen.process.comedian import MESSAGES, TARGET_EMAIL, TARGET_PAGER


class TestComedian(unittest.TestCase):

    def setUp(self):
        self.details = MESSAGES.get("success_details")
        self.in_range_quotas = {
            "api_requests_monthly": {"allowed": 5000, "used": 0},
            "intelligence_downloads_monthly": {"allowed": 5000, "used": 0},
            "intelligence_hunting_rules": {"allowed": 5000, "used": 0},
            "intelligence_retrohunt_jobs_monthly": {"allowed": 5000, "used": 0},
            "intelligence_searches_monthly": {"allowed": 5000, "used": 0}
        }
        self.out_of_range_quotas = {
            "api_requests_monthly": {"allowed": 5000, "used": 5000},
            "intelligence_downloads_monthly": {"allowed": 5000, "used": 0},
            "intelligence_hunting_rules": {"allowed": 5000, "used": 0},
            "intelligence_retrohunt_jobs_monthly": {"allowed": 5000, "used": 0},
            "intelligence_searches_monthly": {"allowed": 5000, "used": 0}
        }
        self.threshold = 0.5
        self.traceback = "Traceback created during exception catch."

        # Constants that use previously declared constants.
        self.exceeded_quota_message = MESSAGES.get("quota_exceeded")\
                                              .format("api_requests_monthly", self.threshold*100, 5000, 5000, 100.0) \
            + "\n" + const.MESSAGE_SEPARATOR + "\n"
        self.parameters = {
                "details": self.details,
                "disable_notifier": True,
                "message": MESSAGES.get("success_short_message"),
                "snapshot": self.in_range_quotas,
                "state": "SUCCESS",
                "subject": MESSAGES.get("success_subject"),
                "success": True,
        }
        self.successful_results = [{
            "details": MESSAGES.get("success_details"),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("success_short_message"),
            "source": "Comedian",
            "result_id": 0,
            "snapshot": self.in_range_quotas,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET_PAGER,
        }, {
            "details": MESSAGES.get("success_details"),
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("success_short_message"),
            "source": "Comedian",
            "result_id": 0,
            "snapshot": self.in_range_quotas,
            "state": "SUCCESS",
            "subject": MESSAGES.get("success_subject"),
            "success": True,
            "target": TARGET_EMAIL,
        },
        ]

    @staticmethod
    def _create_comedian_obj():
        """
        Creates a Comedian object.
        @return: <Comedian> object.
        """
        return Comedian(event=None, context=None)

    @patch("watchmen.process.comedian.Comedian._calculate_threshold")
    @patch("watchmen.process.comedian.Comedian._get_group_info")
    def test_monitor(self, mock_group_info, mock_threshold):
        comedian_obj = self._create_comedian_obj()
        failure_results = [{
            "details": self.exceeded_quota_message,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("failure_short_message"),
            "source": "Comedian",
            "result_id": 0,
            "snapshot": self.out_of_range_quotas,
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": TARGET_PAGER,
        }, {
            "details": self.exceeded_quota_message,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("failure_short_message"),
            "source": "Comedian",
            "result_id": 0,
            "snapshot": self.out_of_range_quotas,
            "state": "FAILURE",
            "subject": MESSAGES.get("failure_subject"),
            "success": False,
            "target": TARGET_EMAIL,
        },
        ]
        exception_results = [{
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("exception_short_message"),
            "source": "Comedian",
            "result_id": 0,
            "snapshot": {},
            "state": "EXCEPTION",
            "subject": MESSAGES.get("exception_subject"),
            "success": False,
            "target": TARGET_PAGER,
        }, {
            "details": MESSAGES.get("exception_details").format(self.traceback),
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": MESSAGES.get("exception_short_message"),
            "source": "Comedian",
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
                "group_quota_info": self.in_range_quotas,
                "tb": "",
                "results": self.successful_results
            },
            {
                "group_quota_info": self.out_of_range_quotas,
                "tb": "",
                "results": failure_results
            },
            {
                "group_quota_info": None,
                "tb": self.traceback,
                "results": exception_results
            }
        ]

        for test in tests:
            mock_group_info.return_value = test.get("group_quota_info"), test.get("tb")
            mock_threshold.return_value = self.threshold

            expected_results = test.get("results")
            returned_results = comedian_obj.monitor()

            returned_pager_result = returned_results[0].to_dict()
            returned_email_result = returned_results[1].to_dict()

            returned_pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_pager_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

            returned_email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned_email_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

            self.assertEqual(expected_results[0], returned_pager_result)
            self.assertEqual(expected_results[1], returned_email_result)

    @patch("watchmen.process.comedian.datetime")
    def test_calculate_threshold(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(year=2019, month=12, day=15, tzinfo=pytz.utc)
        comedian_obj = self._create_comedian_obj()

        # (THRESHOLD_START + (15 * 2)) / 100 = 0.56
        expected_threshold = 0.56
        returned_threshold = comedian_obj._calculate_threshold()

        self.assertEqual(expected_threshold, returned_threshold)

    def test_check_group_info(self):
        comedian_obj = self._create_comedian_obj()
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

            returned = comedian_obj._check_group_info(threshold, quota)

            self.assertEqual(expected_success, returned.get("success"))
            self.assertEqual(expected_exceeded_quotas, returned.get("details"))

    @patch('watchmen.process.comedian.traceback.format_exc')
    def test_check_group_info_exception(self, mock_traceback):
        traceback = self.traceback
        mock_traceback.return_value = traceback
        comedian_obj = self._create_comedian_obj()

        expected_details = MESSAGES.get("quota_exception_details").format(traceback)
        expected = {
            "success": None,
            "details": expected_details
        }
        returned = comedian_obj._check_group_info(self.threshold, {})

        self.assertEqual(expected, returned)

    def test_create_results(self):
        comedian_obj = self._create_comedian_obj()
        expected = self.successful_results
        returned = comedian_obj._create_results(self.parameters)

        returned_pager_result = returned[0].to_dict()
        returned_email_result = returned[1].to_dict()

        returned_pager_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned_pager_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        returned_email_result["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned_email_result["dt_updated"] = "2018-12-18T00:00:00+00:00"

        self.assertEqual(expected[0], returned_pager_result)
        self.assertEqual(expected[1], returned_email_result)

    def test_create_result_parameters(self):
        comedian_obj = self._create_comedian_obj()
        expected = self.parameters
        returned = comedian_obj._create_result_parameters(True, self.details, self.in_range_quotas)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.comedian.requests.get')
    @patch('watchmen.process.comedian.traceback.format_exc')
    def test_get_group_info_exception(self, mock_traceback, mock_request):
        traceback = self.traceback
        mock_request.side_effect = Exception()
        mock_traceback.return_value = traceback
        comedian_obj = self._create_comedian_obj()

        expected = None, traceback
        returned = comedian_obj._get_group_info()

        self.assertEqual(expected, returned)
