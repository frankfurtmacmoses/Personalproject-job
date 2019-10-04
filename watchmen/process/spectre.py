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
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

# Filepath Strings
BUCKET_NAME = settings("spectre.bucket_name", "cyber-intel")
PATH_PREFIX = settings("spectre.path_prefix", "hancock/georgia_tech/")
SNS_TOPIC_ARN = settings('spectre.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

# Message Strings
SUCCESS_MESSAGE = "Georgia Tech Feed data found on S3!"
FAILURE_MESSAGE = "could not be found in {}/{}! " \
                  "Please check S3 and Georgia Tech logs!".format(BUCKET_NAME, PATH_PREFIX)
SUCCESS_SUBJECT = "Spectre Georgia Tech data monitor found everything alright. "
FAIL_SUBJECT_MESSAGE = "Spectre Georgia Tech data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = " not found on S3 in {}/{}! Georgia Tech data is missing, " \
                       "please view the logs!".format(BUCKET_NAME, PATH_PREFIX)
EXCEPTION_SUBJECT = "Spectre for Georgia Tech had an exception!"
EXCEPTION_MESSAGE = 'Spectre for Georgia Tech failed on \n\t"{}" \ndue to ' \
                    'the Exception:\n\n{}\n\nPlease check the logs!'

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
                "subject": FAIL_SUBJECT_MESSAGE,
            },
        }
        parameters = parameter_chart.get(file_found)
        result = self._create_result(
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
            self.logger.info('*' * const.LENGTH_OF_PRINT_LINE)
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
                'details': EXCEPTION_MESSAGE.format(filename, tb),
                'log_details': EXCEPTION_MESSAGE.format(filename, tb),
            },
            False: {
                'details': 'ERROR: {} {}'.format(filename, FAILURE_MESSAGE),
                'log_details': 'File: {} {}'.format(filename, FILE_NOT_FOUND_ERROR),
            },
            True: {
                'details': SUCCESS_MESSAGE,
                'log_details': SUCCESS_MESSAGE,
            }
        }
        status = FILE_STATUS.get(found_file)
        details = status.get('details')
        if status.get('log_details'):
            self.logger.info(status.get('log_details'))
        return details

    def _create_result(self, success, disable_notifier, state, subject, details):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, othrewise false
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
