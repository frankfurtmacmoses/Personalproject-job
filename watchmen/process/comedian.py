"""
Created on November 27, 2019

This Watchman monitors the VirusTotal API to ensure that our team does not go over our monthly quota limit. This
Watchman will send both email and SMS alerts if the used-to-allowed ratio crosses its threshold.

@author: Michael Garcia
@email: garciam@infoblox.com
"""

import hashlib
import hmac
import os
import requests
import traceback
import yaml

from datetime import datetime
from watchmen import const
from watchmen import messages
from watchmen.common.result_svc import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings


ERROR = "ERROR"
CONFIG_NAME = 'api_targets.yaml'
CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), CONFIG_NAME)

GENERIC = 'Generic Quota'
MESSAGES = messages.COMEDIAN
TARGET_EMAIL = "{} Email"
TARGET_PAGER = "{} Pager"


class Comedian(Watchman):
    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()

    def monitor(self) -> [Result]:
        api_targets, tb = self._load_config()
        if tb or api_targets is None:
            details = MESSAGES.get("exception_config_details").format(tb)
            result = self._create_generic_result(False, True, details)
            return [result]

        targets_quota_info = self._get_targets_quota_info(api_targets)
        if not targets_quota_info:
            details = MESSAGES.get("exception_api_details")
            result = self._create_generic_result(False, True, details)
            return [result]

        targets_check_info, tb = self._check_api_quotas(targets_quota_info)
        if tb:
            details = MESSAGES.get("quota_exception_details").format(tb)
            result = self._create_generic_result(False, True, details)
            return [result]

        result_parameters, failure_in_results, exception_in_results = self._create_result_parameters(targets_check_info)

        return self._create_results(result_parameters,  failure_in_results, exception_in_results)


    def _calculate_threshold(self):
        """
        Calculates the used-to-allowed quota threshold based on the current day of the month. The threshold is
        calculated by starting at 28% for the first day of the month, and adding 2% to the threshold each day. By the
        end of the month the threshold will be around 90%.
        :return: The current used-to-allowed quota threshold.
        """
        day = datetime.utcnow().day
        threshold = (THRESHOLD_START + (day * 2)) / 100

        return threshold

    def _check_group_info(self, threshold, group_quota_info):
        """
        Checks the quotas within the group_quota_info to ensure that the values are within the current threshold. If any
        quotas listed in MONTHLY_QUOTAS is over the threshold, an SNS alert will be sent.
        :param threshold: The current used-to-allowed threshold.
        :param group_quota_info: Dictionary of the quotas for the "infoblox" group. These quotas include the Used and
        Allowed values, which is compared against the current used-to-allowed threshold.
        :return: Dictionary containing information about the quota checks. "success" indicates the result of checking
        all the quotas. The "details" is a properly formatted string of all the quotas that exceeded the
        used-to-allowed threshold.
        """
        group_check_info = {
            "success": True,
            "details": ""
        }

        try:
            for quota in MONTHLY_QUOTAS:
                current_quota = group_quota_info[quota]
                used = current_quota["used"]
                allowed = current_quota["allowed"]

                # Multiplying `used` by 1.0 to prevent the decimal being truncated by Python.
                quota_usage = (used * 1.0) / allowed
                if quota_usage >= threshold:
                    exceeded_details = MESSAGES.get("quota_exceeded")\
                                               .format(quota, threshold * 100, used, allowed, quota_usage * 100)

                    group_check_info["details"] += (exceeded_details + "\n" + const.MESSAGE_SEPARATOR + "\n")
                    group_check_info["success"] = False

            return group_check_info
        except Exception as ex:
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()

            group_check_info["details"] = MESSAGES.get("quota_exception_details").format(tb)
            group_check_info["success"] = None

            return group_check_info

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

    def _create_result_parameters(self, success, details, quotas):
        """
        Creates the Result object parameters based on the success of the quota checks.
        :param success: Boolean indicating the result of checking the VirusTotal quotas. True if all quotas were within
        the threshold, False if not, and None if an exception was encountered while attempting to check the quotas.
        :param details: Details about the quota check result.
        :param quotas: Snapshot of the VirusTotal quotas.
        :return: A dictionary containing "details", "disable_notifier", "short_message", "snapshot", "state", "subject",
        and "success".
        """
        parameter_chart = {
            None: {
                "details": details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("exception_short_message"),
                "snapshot": quotas,
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
                "success": False,
            },
            True: {
                "details": MESSAGES.get("success_details"),
                "disable_notifier": True,
                "short_message": MESSAGES.get("success_short_message"),
                "snapshot": quotas,
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
                "success": True,
            },
            False: {
                "details": details,
                "disable_notifier": False,
                "short_message": MESSAGES.get("failure_short_message"),
                "snapshot": quotas,
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
                "success": False,
            },
        }
        parameters = parameter_chart.get(success)
        return parameters

    def _get_group_info(self):
        """
        Performs a GET request to the VirusTotal API to get the quota information for the "infoblox" group.
        :return: The "quotas" dictionary returned from the VirusTotal API. This dictionary contains all the quotas
        to be checked.

        VirusTotal's response value comes in the following format (with a lot of other information that we do not use):
        {"data":
            {"attributes":
                {"quotas":
                    {"api_requests_daily": {"allowed": 5000, "used": 0},
                    "api_requests_hourly": {"allowed": 600000, "used": 0},
                    "api_requests_monthly": {"allowed": 1000000000, "used": 3},
                    "intelligence_downloads_monthly": {"allowed": 300, "used": 3},
                    "intelligence_graphs_private": {"allowed": 0, "used": 0},
                    "intelligence_hunting_rules": {"allowed": 20000, "used": 52},
                    "intelligence_retrohunt_jobs_monthly": {"allowed": 5, "used": 0},
                    "intelligence_searches_monthly": {"allowed": 300, "used": 99},
                    "monitor_storage_bytes": {"allowed": 0, "used": 0},
                    "monitor_storage_files": {"allowed": 0, "used": 0},
                    "monitor_uploaded_bytes": {"allowed": 0, "used": 0},
                    "monitor_uploaded_files": {"allowed": 0, "used": 0}
                    }
                },
         }

         The only part we are interested in is the "quotas" dictionary, so we grab that and return it as the
         "group_quota_information".
        """
        try:
            virustotal_api_response = requests.get(url=GROUP_QUOTA_URL, headers=HEADERS).json()
            group_quota_information = virustotal_api_response["data"]["attributes"]["quotas"]
            return group_quota_information, None
        except Exception as ex:
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb
