"""
Created on November 11, 2019

This Watchman monitors the forevermail S3 folder in the cyber-intel AWS account to ensure a file is uploaded every 10
minutes. If a file is not found or the file size remains the same for 2 files in a row, an SNS alert will be sent. There
is an exception to this rule; the first file of the day "0000.tar.gz" is not uploaded and this is not an error.

@author: Michael Garcia
@email: garciam@infoblox.com
"""
import traceback
from datetime import datetime, timedelta

from watchmen import const
from watchmen import messages
from watchmen.common.result_svc import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils.s3 import get_key, check_unequal_files

BUCKET_NAME = settings("mothman.bucket_name")
MESSAGES = messages.MOTHMAN
PATH_PREFIX = settings("mothman.path_prefix")
S3_DATA_FILE = PATH_PREFIX + "/{}/{}/{}/{}/{}.tar.gz"
TARGET = "ForeverMail"
TEST_PREFIX = settings("mothman.test_prefix")


class Mothman(Watchman):

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()

    def monitor(self) -> [Result]:
        file_info = self._create_path_info()
        file_check_info = self._check_s3_files(file_info)
        success = file_check_info.get("success")
        details = file_check_info.get("details")

        parameters = self._create_result_parameters(success, details)
        result = self._create_result(parameters)
        return [result]

    def _check_s3_files(self, file_info):
        """
        Checks the ForeverMail S3 files to ensure files are being uploaded as expected. The "0000.tar.gz" file does not
        exist, which is not an error. If the latest_file exists and there is any problem retrieving the previous_file,
        information indicating a success is returned because the previous execution of Mothman should have caught the
        problem and sent a notification. This prevents Mothman from sending redundant alerts.
        :param file_info: Dictionary containing the file paths for two S3 files, along with their hour_minute
                          attributes.
        :return: Dictionary containing information about the result of the file checks. This information includes the
        boolean "success" which indicates if the S3 files are being uploaded as expected and the string "details" which
        contains information about the file checks.

        Example:
        {
            "success": True,
            "details": "Details about the file checks"
        }
        """
        latest_file_path = file_info.get("latest_file_path")
        latest_hour_minute = file_info.get("latest_hour_minute")
        previous_file_path = file_info.get("previous_file_path")
        previous_hour_minute = file_info.get("previous_hour_minute")

        try:
            if latest_hour_minute == "0000":
                details = MESSAGES.get("success_latest_hm").format(latest_file_path)
                return {"success": True, "details": details}

            latest_file_obj = get_key(latest_file_path, BUCKET_NAME)
            if latest_file_obj is None:
                details = MESSAGES.get("failure_latest_file_dne").format(latest_file_path)
                return {"success": False, "details": details}

            if previous_hour_minute == "0000":
                details = MESSAGES.get("success_previous_hm")
                return {"success": True, "details": details}

            previous_file_object = get_key(previous_file_path, BUCKET_NAME)
            if previous_file_object is None:
                details = MESSAGES.get("success_previous_file_dne").format(previous_file_path)
                return {"success": True, "details": details}

            unequal_files = check_unequal_files(latest_file_obj, previous_file_object)

            if unequal_files:
                details = MESSAGES.get("success_unequal_files").format(latest_file_path, previous_file_path)
                return {"success": True, "details": details}
            else:
                details = MESSAGES.get("failure_equal_files").format(latest_file_path, previous_file_path)
                return {"success": False, "details": details}

        except Exception as ex:
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception("{}: {}".format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            details = MESSAGES.get("exception_details").format(tb)
            return {"success": None, "details": details}

    def _convert_datetime_to_dict(self, datetime_string):
        """
        Takes in a datetime string with the format of "%Y-%m-%d-%H-%M" and turns it into a dictionary of all the time
        attributes. This method also rounds the minute attribute down to the nearest multiple of 10 to match the
        expected format of the file in S3.
        :param datetime_string: A datetime string with the format of "%Y-%m-%d-%H-%M". For example: 2019-01-01-00-05
        :return: A dictionary with each time attribute: year, month, day, hour, and minute(rounded down to the nearest
                 multiple of 10. For example if the minute is 36, we want it to be 30.)
        Example: {"year": "2019", "month": "12", "day": "15", "hour": "00", "minute": "00"}
        """
        time_info_keys = ["year", "month", "day", "hour", "minute"]

        time_list = datetime_string.split("-")

        # By changing the second digit in minutes to 0 we are essentially rounding down to the nearest multiple of 10,
        # which matches the format of the S3 file we are looking for.
        time_list[4] = time_list[4][:-1] + "0"

        time_info = dict(zip(time_info_keys, time_list))

        return time_info

    def _create_path_info(self):
        """
        Creates a dictionary containing the file paths of the two S3 files to be checked, along with the hour_minute
        attribute of each file. The reason for having a separate hour_minute is to be able to check for when one of the
        files is "0000.tar.gz" in _check_s3_files.
        :return: dictionary containing all required file path information to check files in S3.

        Example:
        {
            "latest_file_path": ""malspam/forevermail/2019/11/08/00/0020.tar.gz"",
            "latest_hour_minute": "0020",
            "previous_file_path": ""malspam/forevermail/2019/11/08/00/0010.tar.gz"",
            "previous_hour_minute": "0010"
        }
        """
        path_info = {
            "latest_file_path": "",
            "latest_hour_minute": "",
            "previous_file_path": "",
            "previous_hour_minute": ""
        }

        previous_time, latest_time = self._get_times_to_check()
        previous_time_dict = self._convert_datetime_to_dict(previous_time)
        latest_time_dict = self._convert_datetime_to_dict(latest_time)

        previous_hour_minute = previous_time_dict.get("hour") + previous_time_dict.get("minute")
        path_info["previous_hour_minute"] = previous_hour_minute

        latest_hour_minute = latest_time_dict.get("hour") + latest_time_dict.get("minute")
        path_info["latest_hour_minute"] = latest_hour_minute

        path_info["previous_file_path"] = S3_DATA_FILE.format(previous_time_dict.get("year"),
                                                              previous_time_dict.get("month"),
                                                              previous_time_dict.get("day"),
                                                              previous_time_dict.get("hour"),
                                                              previous_hour_minute)
        path_info["latest_file_path"] = S3_DATA_FILE.format(latest_time_dict.get("year"),
                                                            latest_time_dict.get("month"),
                                                            latest_time_dict.get("day"),
                                                            latest_time_dict.get("hour"),
                                                            latest_hour_minute)

        return path_info

    def _create_result(self, parameters):
        """
        Creates a Result object with the variables within the parameters dictionary.
        :param parameters: Dictionary of Result attributes corresponding to the result of the file checks.
        :return: Result object.
        """
        result = Result(
            details=parameters.get("details"),
            disable_notifier=parameters.get("disable_notifier"),
            message=parameters.get("message"),
            snapshot={},
            source=self.source,
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            success=parameters.get("success"),
            target=parameters.get("target"),
        )
        return result

    def _create_result_parameters(self, success, details):
        """
        Creates a dictionary of Result object attributes corresponding to the result of the file checks.
        :param success: Boolean indicating success of the file checks. True if successful, False if unsuccessful,
                        None if exception.
        :param details: String containing details of the file check.
        :return: A dictionary containing "details", "disable_notifier", "message", "state", "subject", "success", and
                "target".
        """
        parameter_chart = {
            None: {
                "details": details,
                "disable_notifier": False,
                "message": MESSAGES.get("exception_subject"),
                "state": Watchman.STATE.get("exception"),
                "subject": MESSAGES.get("exception_subject"),
                "success": False,
                "target": TARGET
            },
            True: {
                "details": details,
                "disable_notifier": True,
                "message": MESSAGES.get("success_short_message"),
                "state": Watchman.STATE.get("success"),
                "subject": MESSAGES.get("success_subject"),
                "success": True,
                "target": TARGET
            },
            False: {
                "details": details,
                "disable_notifier": False,
                "message": MESSAGES.get("failure_short_message"),
                "state": Watchman.STATE.get("failure"),
                "subject": MESSAGES.get("failure_subject"),
                "success": False,
                "target": TARGET
            },
        }
        parameters = parameter_chart.get(success)
        return parameters

    def _get_times_to_check(self):
        """
        Returns two datetime strings that represent the time 10 minutes ago and another string for 20 minutes ago. The
        datetime strings are formatted to have padded zeros in the front to match the format of the dates used in the
        ForeverMail S3 folder.
        :return: Two datetime strings that will be used to create file paths in "_create_path_info".
        latest_time: datetime string that represents the time 10 minutes ago.
        previous_time: datetime string that represents the time 20 minutes ago.

        Example of returned values:
        "2019-01-01-16-45"
        """
        latest_time = (datetime.utcnow() - timedelta(minutes=10)).strftime("%Y-%m-%d-%H-%M")
        previous_time = (datetime.utcnow() - timedelta(minutes=20)).strftime("%Y-%m-%d-%H-%M")

        return previous_time, latest_time
