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
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

SUCCESS_MESSAGE = "NOH/D Feeds are up and running!"
ERROR = "ERROR: "
FAILURE_DOMAIN_START = ERROR + "The newly observed domains feed has gone down!"
FAILURE_HOSTNAME_START = ERROR + "The newly observed hostname feed has gone down!"
FAILURE_BOTH_START = ERROR + "Both hostname and domains feed have gone down!"
FAILURE_GENERAL_MESSAGE = "{}\nPlease check the Response Guide for Moloch in watchmen documents: " \
                          "https://docs.google.com/document/d/1to0ZIaU4E-XRbZ8QvNrPLe4" \
                          "30bWWxRAPCkWk68pcwjE/edit#heading=h.6dcje1sj7gup"
FAILURE_DOMAIN = FAILURE_GENERAL_MESSAGE.format(FAILURE_DOMAIN_START)
FAILURE_HOSTNAME = FAILURE_GENERAL_MESSAGE.format(FAILURE_HOSTNAME_START)
FAILURE_BOTH = FAILURE_GENERAL_MESSAGE.format(FAILURE_BOTH_START)

SUCCESS_SUBJECT = "Moloch watchman found Hostnames and Domains feeds works okay!"
FAILURE_SUBJECT = "Moloch watchmen detected an issue with NOH/D feed!"

EXCEPTION_SUBJECT = "Moloch watchmen reached an exception!"
EXCEPTION_MESSAGE = "The newly observed domain feeds and hostname feeds reached an exception during the file checking" \
                    " process due to the following:\n\n{}\n\nPlease look at the logs for more insight."

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
            self.logger.info('*' * const.LENGTH_OF_PRINT_LINE)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, None, tb

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
        status, details_type = SUCCESS_MESSAGE, True
        if domain_check is None or hostname_check is None:
            return EXCEPTION_MESSAGE.format(tb), None

        if not domain_check or not hostname_check:
            if not domain_check and not hostname_check:
                status, details_type = FAILURE_BOTH, False
            elif not domain_check:
                status, details_type = FAILURE_DOMAIN, False
            elif not hostname_check:
                status, details_type = FAILURE_HOSTNAME, False
        return status, details_type

    def _create_result(self, success, disable_notifier, state, subject, details):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, otherwise false
        @param state: <str> state of the monitor check
        @param subject: <str> subject for the notification
        @param details: <str> content for the notification
        @return: <Result> result based on the parameters
        """
        result = Result(
            success=success,
            disable_notifier=disable_notifier,
            state=state,
            subject=subject,
            source=self.source,
            target=TARGET,
            details=details)
        return result

    def monitor(self) -> Result:
        """
        checks whether Newly Observed Hostnames and Newly Observed Domains feeds are on S3.
        @return: <Result> Result object
        """
        domain_check, host_check, tb = self._get_check_results()
        details, msg_type = self._create_details(host_check, domain_check, tb)
        parameter_chart = {
            None: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": EXCEPTION_SUBJECT,
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": SUCCESS_SUBJECT,
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": FAILURE_SUBJECT,
            },
        }
        parameters = parameter_chart.get(msg_type)
        result = self._create_result(
            success=parameters.get("success"),
            disable_notifier=parameters.get("disable_notifier"),
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            details=details
        )
        return [result]

# the following blocked out code is for local testing in the future


# def run():
#     moloch_obj = Moloch()
#     result = moloch_obj.monitor()
#     print(result.to_dict())
#
#
# if __name__ == "__main__":
#     run()
