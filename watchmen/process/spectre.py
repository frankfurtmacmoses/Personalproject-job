"""
watchmen.process/spectre.py

This class monitors S3 ensuring data from Georgia Tech Feed is properly transferred.
If data is not found or has a value of 0, an alert is sent out.

@author: Kayla Ramos
@email: kramos@infoblox.com
@created: January 22, 2019
@updated: July 1, 2019

Refactored on July 2nd, 2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""

from datetime import datetime, timedelta
import pytz
import traceback
from typing import Tuple

from watchmen import const
from watchmen import messages
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

MESSAGES = messages.SPECTRE
# Filepath Strings
BUCKET_NAME = settings("spectre.bucket_name", "cyber-intel")
PATH_PREFIX = settings("spectre.path_prefix", "hancock/georgia_tech/")
SNS_TOPIC_ARN = settings('spectre.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

# Watchman profile
TARGET = "Georgia Tech S3"


class Spectre(Watchman):

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()
        pass

    def monitor(self) -> [Result]:
        """
        Checks whether or not the file is on S3.
        @return: <result> Result Object
        """
        filename = self._create_s3_filename()
        file_found, tb = self._check_if_found_file(filename)
        details = self._create_details(filename, file_found, tb)
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
                "subject": MESSAGES.get("failure_subject_message"),
            },
        }
        parameters = parameter_chart.get(file_found)
        result = self._create_result(
            short_message=parameters.get("short_message"),
            success=parameters.get("success"),
            disable_notifier=parameters.get("disable_notifier"),
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            details=details
        )
        return [result]

    def _check_if_found_file(self, filename) -> Tuple[bool, str]:
        """
        Check if the file for yesterday is found on the Georgia Tech feed
        @param filename: name of the file to check
        @return: whether or not the file was found; otherwise, None upon exception
        """
        file_path = '{}{}'.format(PATH_PREFIX, filename)

        try:
            found_file = validate_file_on_s3(BUCKET_NAME, file_path)
            return found_file, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _create_details(self, filename, found_file, tb):
        """
        Depending if the file was found or not, send an email alert if it was not or an error occurred
        @param found_file: whether or not the file was found (boolean) or None if there was an exception
        @param filename: name of the file that was checked (used for notification purposes)
        @return: the status of the check
        """
        FILE_STATUS = {
            None: {
                'details': MESSAGES.get("exception_message").format(filename, tb),
                'log_details': MESSAGES.get("exception_message").format(filename, tb),
            },
            False: {
                'details': 'ERROR: {} {}'.format(filename, MESSAGES.get("failure_message")
                                                                   .format(BUCKET_NAME, PATH_PREFIX)),
                'log_details': 'File: {} {}'.format(filename, MESSAGES.get("file_not_found_error")
                                                                      .format(BUCKET_NAME, PATH_PREFIX)),
            },
            True: {
                'details': MESSAGES.get("success_message"),
                'log_details': MESSAGES.get("success_message"),
            }
        }
        status = FILE_STATUS.get(found_file)
        details = status.get('details')
        if status.get('log_details'):
            self.logger.info(status.get('log_details'))
        return details

    def _create_result(self, short_message, success, disable_notifier, state, subject, details):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, othrewise false
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

    def _create_s3_filename(self):
        """
        Creates yesterday's s3 filename
        :return: filename
        """
        now = datetime.now(pytz.utc)
        yesterday = now - timedelta(days=1)
        filename = yesterday.strftime('%Y') + "/" + \
            yesterday.strftime('%m') + "/gt_mpdns_" + yesterday.strftime("%Y%m%d") + ".zip"
        return filename
