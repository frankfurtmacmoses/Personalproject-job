"""
watchmen/models/moloch.py

Created on July 19, 2018

This script is designed to monitor Newly Observed Hostnames and
Newly Observed Domains feeds. This should run every hour and
confirm that the feeds have been running within the past hour.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

Refactored on July 11, 2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""

# Python imports
import traceback
import pytz
from datetime import datetime, timedelta

# Cyberint imports
from watchmen import const
from watchmen import messages
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

MESSAGES = messages.MOLOCH
BUCKET_NAME = settings('moloch.bucket_name', "deteque-new-observable-data")
DOMAINS_PATH = settings('moloch.domain_name', "NewlyObservedDomains")
HOSTNAME_PATH = settings('moloch.hostname_path', "NewlyObservedHostname")

SNS_TOPIC_ARN = settings('moloch.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

FILE_START = "ZMQ_Output_"
FILE_EXT = ".txt"

# Watchman profile
TARGET = "Newly Observed Data"


class Moloch(Watchman):
    """
    Class of Moloch
    """

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()
        pass

    def monitor(self) -> [Result]:
        """
        checks whether Newly Observed Hostnames and Newly Observed Domains feeds are on S3.
        @return: <Result> Result object
        """
        domain_check, host_check, tb = self._get_check_results()
        details, msg_type = self._create_details(host_check, domain_check, tb)
        parameter_chart = {
            None: {
                "short_message": MESSAGES.get("exception_short_message"),
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
            },
            True: {
                "short_message": MESSAGES.get("success_message"),
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
            },
            False: {
                "short_message": MESSAGES.get("failure_short_message"),
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
            },
        }
        parameters = parameter_chart.get(msg_type)
        result = self._create_result(
            short_message=parameters.get("short_message"),
            success=parameters.get("success"),
            disable_notifier=parameters.get("disable_notifier"),
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            details=details
        )
        return [result]

    def _check_for_existing_files(self, file_path, check_time):
        """
        Searches through file path and stops when it has found a file.
        NOTE: This process doesn't check that all 60 files exist, but that at least,
              1 exists. NOH/D feeds are up or stay down forever.
        @param file_path: <str> the file path
        @param check_time: <str> the time stamp for files to be checked
        @return: <bool> if any file was found
        """
        file_found = False
        count = 0
        # Goes through until it finds a file or all 60 files do not appear in S3.
        while not file_found and count != 60:
            key = file_path + check_time.strftime("%Y_%-m_%-d_%-H_%-m") + FILE_EXT
            file_found = validate_file_on_s3(BUCKET_NAME, key)
            check_time += timedelta(minutes=1)
            count += 1
        return file_found

    def _create_details(self, hostname_check, domain_check, tb):
        """
        Depending on the status of Newly Observed Hostnames and
        Newly Observed Domains feeds, send details of failure for
        the situations where either of hostnames or domain feeds
        is failed or both of them failed. Send successful details
        when both of them are added successfully. Exception details
        when exception happened in the process.

        @param hostname_check: <bool> status of newly observed hostnames
        @param domain_check: <bool> status of newly observed domains
        @param tb: <str> traceback of exception during the process, None if no exception
        @return: <str> <bool>
        <str>: details
        <bool>: type of details, True for success, False for failure, None for exception
        """
        status, details_type = MESSAGES.get("success_message"), True
        if domain_check is None or hostname_check is None:
            return MESSAGES.get("exception_message").format(tb), None

        if not domain_check or not hostname_check:
            if not domain_check and not hostname_check:
                status, details_type = MESSAGES.get("failure_both"), False
            elif not domain_check:
                status, details_type = MESSAGES.get("failure_domain"), False
            elif not hostname_check:
                status, details_type = MESSAGES.get("failure_hostname"), False
        return status, details_type

    def _create_result(self, short_message, success, disable_notifier, state, subject, details):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, otherwise false
        @param state: <str> state of the monitor check
        @param subject: <str> subject for the notification
        @param details: <str> content for the notification
        @return: <Result> result based on the parameters
        """
        result = Result(
            short_message=short_message,
            success=success,
            disable_notifier=disable_notifier,
            state=state,
            subject=subject,
            watchman_name=self.watchman_name,
            target=TARGET,
            details=details)
        return result

    def _get_check_results(self):
        """
        checks if the domain and hostname contain existing files one hour ago
        @return: <bool> <bool> <str>
        <bool>: the status of the domain or None upon exception
        <bool>: the status of the host name or None upon exception
        <str>: traceback in the process
        """
        # Feeds are on both the same time
        check_time = datetime.now(pytz.utc) - timedelta(hours=1)
        # Hyphen before removes 0 in front of values. Eg 2018_07_06 becomes 2018_7_6
        parsed_date_time = check_time.strftime("%Y_%-m_%-d").split('_')
        file_path = '/' + parsed_date_time[0] + '/' + parsed_date_time[1] + '/' + parsed_date_time[2] + '/' + FILE_START

        try:
            domain_check = self._check_for_existing_files(DOMAINS_PATH + file_path, check_time)
            hostname_check = self._check_for_existing_files(HOSTNAME_PATH + file_path, check_time)
            return domain_check, hostname_check, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, None, tb
