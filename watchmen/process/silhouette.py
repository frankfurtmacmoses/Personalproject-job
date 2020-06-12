"""
watchmen/models/silhouette.py

Created on July 18, 2018

This script is designed to check the lookalike feed daily and
ensure that data is coming through into S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

Refactored on July 9, 2019

@author Jinchi Zhang
@email jzhang@infoblox.com
"""

# Python imports
from datetime import datetime, timedelta
import json
import pytz
import traceback

# Cyberint imports
from watchmen import const
from watchmen.utils.s3 import get_file_contents_s3
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.common.watchman import Watchman

SUCCESS_MESSAGE = "Lookalike2 algorithm is up and running!"
FAILURE_MESSAGE = "Lookalike2 algorithm never added files yesterday! " \
                  "The algorithm may be down or simply did not complete!"
SUCCESS_SUBJECT = "Silhouette: Lookalike2 files have been successfully detected in S3!"
FAILURE_SUBJECT = "FAILURE: Silhouette detected an issue with the Lookalike2 algorithm!"
SNS_TOPIC_ARN = settings("silhouette.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

EXCEPTION_SUBJECT = "EXCEPTION: Silhouette failed to check the Lookalike2 algorithm!"
EXCEPTION_MESSAGE = 'Silhouette for lookalike2 algorithm failed on \n\t"{}" \ndue to ' \
                    'the Exception:\n\n{}\n\nPlease check the logs!'
EXCEPTION_SHORT_MESSAGE = "Silhouette for lookalike2 algorithm failed due to an exception, please check the logs!"
COMPLETED_STATUS = "completed"

BUCKET_NAME = settings("silhouette.bucket_name", "cyber-intel")
PATH_PREFIX = settings("silhouette.path_prefix", "analytics/lookalike2/prod/status/")
STATUS_FILE = "status.json"

# Watchman profile
TARGET = "Lookalike Feed S3"


class Silhouette(Watchman):

    # pylint: disable=unused-argument
    def __init__(self, event, context):
        super().__init__()
        self.filename = self._get_file_name()
        pass

    def monitor(self) -> [Result]:
        """
        Checks whether or not the lookalike feed is on S3 and completed.
        @return: <result> Result Object.
        """
        is_status_valid, tb = self._check_process_status()
        details = self._create_details(self.filename, is_status_valid, tb)
        parameter_chart = {
            None: {
                "short_message": EXCEPTION_SHORT_MESSAGE,
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
                "subject": EXCEPTION_SUBJECT,
            },
            True: {
                "short_message": SUCCESS_MESSAGE,
                "success": True,
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
                "subject": SUCCESS_SUBJECT,
            },
            False: {
                "short_message": FAILURE_MESSAGE,
                "success": False,
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
                "subject": FAILURE_SUBJECT,
            },
        }
        parameters = parameter_chart.get(is_status_valid)
        result = self._create_result(
            short_message=parameters.get("short_message"),
            success=parameters.get("success"),
            disable_notifier=parameters.get("disable_notifier"),
            state=parameters.get("state"),
            subject=parameters.get("subject"),
            details=details
        )
        return [result]

    def _check_process_status(self):
        """
        Checks the status of the process check.

        @return: <bool> <str>
            <bool> whether or not the process succeeded; otherwise, None upon exception
            <str> traceback in the process
        """
        try:
            is_status_valid = self._process_status()
            return is_status_valid, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _create_details(self, filename, is_status_valid, tb):
        """
        Depending on if the status of lookalike feed, send an email alert if it was not or an error occurred
        @param is_status_valid: whether or not the lookalike feed has good status or None if there was an exception
        @param filename: name of the file that was checked (used for notification purposes)
        @return: <str> the status of the check
        """
        FILE_STATUS = {
            None: {
                'details': EXCEPTION_MESSAGE.format(filename, tb),
                'log_details': EXCEPTION_MESSAGE.format(filename, tb),
            },
            False: {
                'details': 'ERROR: {}\n{}'.format(filename, FAILURE_MESSAGE),
                'log_details': 'File: {}{}'.format(filename, FAILURE_MESSAGE),
            },
            True: {
                'details': SUCCESS_MESSAGE,
                'log_details': SUCCESS_MESSAGE,
            }
        }
        status = FILE_STATUS.get(is_status_valid)
        details = status.get('details')
        if status.get('log_details'):
            self.logger.info(status.get('log_details'))
        return details

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

    def _get_file_name(self):
        """
        Get the name of file being checked.
        @return: <str> file name
        """
        check_time = (datetime.now(pytz.utc) - timedelta(days=1)).strftime("year=%Y/month=%m/day=%d/")
        filename = PATH_PREFIX + check_time + STATUS_FILE
        return filename

    def _process_status(self):
        """
        Checks timestamp of previous day for lookalike feed files being dropped into.
        S3. Status.json has a state which determines if the process was successful or not.

        @return: <bool> whether the process finished or not
        """
        is_completed = False
        file_contents = get_file_contents_s3(BUCKET_NAME, self.filename)
        if file_contents:
            status_json = json.loads(file_contents)
            if status_json.get('state') == COMPLETED_STATUS:
                is_completed = True
        return is_completed
