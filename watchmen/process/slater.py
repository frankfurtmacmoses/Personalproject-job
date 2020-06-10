"""
Created on April, 2020

This Watchman monitors the DomainTools API to ensure that our team does not go over our monthly quota limit. This
Watchman will send both email and SMS alerts if the usage crosses its threshold.

@author: Samyama Yathiraju
@email: syathiraju@infoblox.com
"""
import json
import hmac
import hashlib
import requests
import traceback
from datetime import datetime

from watchmen import const
from watchmen import messages
from watchmen.common.result_svc import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings


API_USERNAME = settings("slater.api_username")
API_KEY = settings("slater.api_key")
HOST = settings("slater.host")
URI = settings("slater.uri")
MESSAGES = messages.SLATER
TARGET_EMAIL = "DomainTools Email"
TARGET_PAGER = "DomainTools Pager"
THRESHOLD_START = settings("slater.threshold_start", 50)


class Slater(Watchman):

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()

    def monitor(self) -> [Result]:
        threshold = self._calculate_threshold()
        domaintool_quota_info, tb = self._get_quotas()

        if not domaintool_quota_info:
            results = self._create_exception_results(tb)
            return results

        quota_check_info = self._check_quota(threshold, domaintool_quota_info)
        parameters = self._create_result_parameters(quota_check_info.get("success"),
                                                    quota_check_info.get("details"),
                                                    domaintool_quota_info)
        results = self._create_results(parameters)

        return results

    def _create_exception_results(self, tb):
        details = MESSAGES.get("exception_details").format(tb)
        parameters = self._create_result_parameters(None, details, {})
        return self._create_results(parameters)

    def _calculate_threshold(self):
        """
        Calculates the API quota threshold based on the current day of the month. The threshold is
        calculated by starting at 50% for the first day of the month and adding 1% to the threshold each day. By the
        end of the month, the threshold will be around 80%.
        :return: The current allowed quota threshold.
        """
        day = datetime.utcnow().day
        threshold = (THRESHOLD_START + day) / 100

        return threshold

    def _check_quota(self, threshold, domaintool_quota_info):
        """
        Checks the quotas within the domaintool_quota_info to ensure that the values are within the current threshold.
        If any quotas are over the threshold, an SNS alert will be sent.
        :param threshold: The current allowed threshold.
        :param domaintool_quota_info: dictionary of products having limit values
        :return: Dictionary containing information about the quota checks. "success" indicates the result of checking
        all the quotas. The "details" contains info of all the quotas exceeded.
        """
        quota_check_info = {
            "success": True,
            "details": ""
        }

        for current_quota in domaintool_quota_info:
            per_month_limit = current_quota['per_month_limit']
            if per_month_limit is not None:
                limit = int(per_month_limit.encode('utf-8'))
                used = int(current_quota['usage']['month'].encode('utf-8'))

                quota_usage = round(used / limit, 2)
                if quota_usage > threshold:
                    exceeded_details = MESSAGES.get("quota_exceeded")\
                        .format(current_quota['id'], threshold * 100, used, limit, quota_usage * 100)

                    quota_check_info["details"] += (exceeded_details + "\n" + const.MESSAGE_SEPARATOR + "\n")
                    quota_check_info["success"] = False

        return quota_check_info

    def _create_results(self, parameters):
        """
        Creates and returns list of the Result objects. This list includes the Result object for the pager SNS topic and
        a Result object for the email SNS topic.
        :param parameters: Dictionary of Result attributes corresponding to the result of the quota checks.
        :return: List of Result objects: [ pager_result, email_result ]
        """
        pager_result = Result(
            details=parameters.get("details"),
            disable_notifier=parameters.get("disable_notifier"),
            short_message=parameters.get("short_message"),
            snapshot=parameters.get("snapshot"),
            watchman_name=self.watchman_name,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            success=parameters.get("success"),
            target=TARGET_PAGER,
        )
        email_result = Result(
            details=parameters.get("details"),
            disable_notifier=parameters.get("disable_notifier"),
            short_message=parameters.get("short_message"),
            snapshot=parameters.get("snapshot"),
            watchman_name=self.watchman_name,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            success=parameters.get("success"),
            target=TARGET_EMAIL,
        )
        return [pager_result, email_result]

    def _create_result_parameters(self, success, details, quotas_check_info):
        """
        Creates the Result object parameters based on the success of the quota checks.
        :param success: Boolean indicating the result of checking the DomainTool quotas.
        True - if all quotas were within the threshold
        False - if quotas are not within the threshold
        None - if an exception was encountered while attempting to check the quotas.
        :param details: Details about the quota check result.
        :param quotas: Snapshot of the DomainTool quotas.
        :return: A dictionary containing "details", "disable_notifier", "short_message", "state",
        "subject" and "success".
        """
        parameter_chart = {
            None: {
                "details": details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("exception_message"),
                "snapshot": quotas_check_info,
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
                "success": False,
            },
            True: {
                "details": MESSAGES.get("success_details"),
                "disable_notifier": True,
                "short_message": MESSAGES.get("success_message"),
                "snapshot": quotas_check_info,
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
                "success": True,
            },
            False: {
                "details": details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("failure_message"),
                "snapshot": quotas_check_info,
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
                "success": False,
            },
        }
        parameters = parameter_chart.get(success)
        return parameters

    def _timestamp(self):
        return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')

    def _sign(self, timestamp, uri):
        params = ''.join([API_USERNAME, timestamp, URI])
        return hmac.new(API_KEY.encode('utf-8'), params.encode('utf-8'), digestmod=hashlib.sha1).hexdigest()

    def _get_quotas(self):
        """
        Performs a GET request to the DomainTools API to get the quota information.
        :return: A list of dictionary which contains the quotas to be checked.
        "Example response"
        {"response":
            {"account":
                {"active": True, "api_username": "IID_dev"},
                "products": [
                    {"absolute_limit": None, "expiration_date": "2021-02-02", "id": "domain-profile",
                    "per_minute_limit": "120", "per_month_limit": None, "usage": {"month": "0", "today": "0"}},
                    {"absolute_limit": None, "expiration_date": "2021-02-02", "id": u"whois",
                    "per_minute_limit": "480", "per_month_limit": "1000000",
                    "usage": {"month": "0", "today": "0"}},
                    {"absolute_limit": None, "expiration_date": "2021-02-02", "id": "whois-history",
                    "per_minute_limit": "30", "per_month_limit": "1000",
                    "usage": {"month": "1", "today": "0"}},
                             ]
            }
        }
        """
        try:
            timestamp = self._timestamp()
            signature = self._sign(timestamp, URI)
            domaintool_response = requests.get(
                'http://{0}{1}?api_username={2}&signature={3}&timestamp={4}'.
                format(HOST, URI, API_USERNAME, signature, timestamp)
            )
            domaintool_quota_info = (domaintool_response.content).decode("utf-8")
            return (json.loads(domaintool_quota_info))['response']['products'], None
        except Exception as ex:
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
