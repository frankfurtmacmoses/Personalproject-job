"""
Created on May 26th, 2020
@author: Rita Li
@email: rili@infoblox.com

This Watchman will complete a weekly file check of the smartlist feeds: ATC, NIOS, Farsight, Umbrella and Majestic.
If the file(s) do not exist or an exception occurs, an email notification is sent to identify the failed feeds
and its prefixes.
"""

import traceback
from datetime import datetime, timedelta

from watchmen import const
from watchmen import messages
from watchmen.common.watchman import Watchman
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3

BUCKET = settings("crookshanks.bucket_name", "cyber-intel")
MESSAGES = messages.CROOKSHANKS
PREFIX = settings("crookshanks.path_prefix", "whitelist/smartlisting/prod/smartlist/")
SOURCES = ["atc", "farsight", "majestic", "nios", "umbrella"]
TARGET = "Smartlisting"


class Crookshanks(Watchman):

    def __init__(self, event, context):
        super().__init__()
        pass

    def monitor(self) -> [Result]:
        """
        Will monitor if the files exists and records the details of the outcome
        """
        scenarios = self.check_s3_files()
        file_exists, check_result = self.create_details(scenarios)
        result_parameter = self.create_result_parameters(check_result, file_exists)
        result = self.create_result(result_parameter)
        return [result]

    def check_s3_files(self):
        """
        Checks if the weekly smartlisting feeds are uploading the files into S3 as expected.
        Depending on the outcome of check, the following will occur:
            If not found, the source and prefix is appended to a list mapped to failure.
            However, if an exception occurs, the source and traceback is appended to a list mapped to exception.
        :returns: Dictionary to record the outcomes by the results
            Ex:
            scenarios = {
                "failures": ["prefix + filename"],
                "exceptions": [{source: tb}]
        }
        """
        scenarios = {
            "failures": [],
            "exceptions": []
        }
        for source in SOURCES:
            full_path = self.create_full_path(source)
            try:
                file_exists = validate_file_on_s3(BUCKET, full_path)
                if not file_exists:
                    scenarios["failures"].append(full_path)
            except Exception as ex:
                self.logger.info(const.MESSAGE_SEPARATOR)
                self.logger.exception(traceback.extract_stack())
                self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
                tracebacks = traceback.format_exc()
                tb = tracebacks.replace('\n', '')
                exception_dict = {source: tb}
                scenarios["exceptions"].append(exception_dict)
        return scenarios

    def create_details(self, scenarios):
        """
        This will draft a record and email notification specifying the details of the outcome.
        If the outcome results in a failure and/or exception, an email is sent to the subscribers with its details.
        However, if all feeds are successful, an email is not required to notify the subscribers but will be recorded.
        :param scenarios: Dictionary of the recorded outcomes categorized by the results of the check
        :return: file_exists: Boolean indicating True (successful if found), False (failure if not found or if not found
        and an error occurs), and None (if an error occurs)
        :return: check_result: Dictionary of the messaging (subject, message, details)
        """
        exception_string = ""
        for path in scenarios['exceptions']:
            exception_string += '{}\n\n'.format(path)
        fail_string = '\n'.join(scenarios['failures'])

        if scenarios["failures"] and scenarios["exceptions"]:
            check_result = {"subject": MESSAGES.get("failure_exception_subject"),
                            "details": MESSAGES.get("failure_exception_message").format(fail_string, exception_string),
                            "log_messages": MESSAGES.get("log_fail_exception_msg").format(fail_string,
                                                                                          exception_string)}
            return False, check_result

        if scenarios["failures"]:
            check_result = {"subject": MESSAGES.get("failure_subject"),
                            "details": MESSAGES.get("failure_message").format(fail_string),
                            "log_messages": MESSAGES.get("log_failure_message").format(fail_string)}
            return False, check_result

        if scenarios["exceptions"]:
            check_result = {"subject": MESSAGES.get("exception_subject"),
                            "details": MESSAGES.get("exception_message").format(exception_string),
                            "log_messages": MESSAGES.get("log_exception_message").format(exception_string)}
            return None, check_result

        check_result = {"subject": MESSAGES.get("success_subject"),
                        "details": MESSAGES.get("success_message"),
                        "log_messages": MESSAGES.get("success_message")}
        return True, check_result

    def create_full_path(self, source):
        """
        Creates the file name and prefix of each source
        :returns: a concatenated string of the prefix and file name
        """
        year = datetime.utcnow().strftime('%Y')
        file_date = (datetime.utcnow() - timedelta(days=1)).strftime('%Y%m%d')
        path_prefix = (PREFIX + "src={}/year={}/").format(source, year)
        file_name = "smartlist_{}_{}.csv".format(file_date, source)
        return path_prefix+file_name

    def create_result(self, result_parameter):
        """
        Creating a result object derived from the outcome of the result_parameter
        :param result_parameter: Provides the result parameters based on the outcome
        :return: Result Object
        """
        result = Result(
            success=result_parameter.get("success"),
            disable_notifier=result_parameter.get("disable_notifier"),
            subject=result_parameter.get("subject"),
            short_message=result_parameter.get("short_message"),
            details=result_parameter.get("details"),
            state=result_parameter.get("state"),
            target=result_parameter.get("target"),
            watchman_name=self.watchman_name)
        return result

    def create_result_parameters(self, check_result, file_exists):
        """
        Creating a parameter chart to categorize the possible results while
        returning the details of the outcome
        :param check_result: Dictionary of the messaging (subject, message, details)
        :param file_exists: Boolean indicating success (if found, True), failure (if not found, False),
        exception (if an error occurs, None)
        :return: Dictionary of the result parameters
        """
        parameter_chart = {
            None: {
                "success": False,
                "disable_notifier": False,
                "subject": check_result.get("subject"),
                "short_message": check_result.get("log_messages"),
                "details": check_result.get("details"),
                "state": Watchman.STATE.get("exception"),
                "target": TARGET
            },
            True: {
                "success": True,
                "disable_notifier": True,
                "subject": check_result.get("subject"),
                "short_message": check_result.get("log_messages"),
                "details": check_result.get("details"),
                "state": Watchman.STATE.get("success"),
                "target": TARGET
            },
            False: {
                "success": False,
                "disable_notifier": False,
                "subject": check_result.get("subject"),
                "short_message": check_result.get("log_messages"),
                "details": check_result.get("details"),
                "state": Watchman.STATE.get("failure"),
                "target": TARGET
            },
        }
        result_parameter = parameter_chart.get(file_exists)
        return result_parameter
