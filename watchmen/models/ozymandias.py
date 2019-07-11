"""
watchman/models/ozymandias.py

Created on June 19, 2018

This script is meant to monitor S3. This script will check that neustar has a file added daily
to ensure proper data flow. Runs once a day looking for these files.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

refactored on 07/10/2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""

import pytz
import traceback

from datetime import datetime, timedelta
from watchmen.utils.logger import get_logger
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

BUCKET_NAME = settings("ozymandias.bucket_name", "cyber-intel")
PATH_PREFIX = settings("ozymandias.path_prefix", "hancock/neustar/")
FILE_NAME = (datetime.now(pytz.utc) - timedelta(days=2)).strftime("%Y%m%d").replace('/', '') + '.compressed'
FILE_PATH = PATH_PREFIX + FILE_NAME
LOGGER = get_logger("Ozymandias", settings('logging.level', 'INFO'))
SNS_TOPIC_ARN = settings('ozymandias.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

SUCCESS_SUBJECT = "Ozymandias watchman found Neustar file added successfully!"
SUCCESS_MESSAGE = "Neustar data found on S3! File found: " + FILE_NAME
FAILURE_MESSAGE = "ERROR: " + FILE_NAME + " could not be found in hancock/neustar! Please check S3 and neustar VM!"
FAILURE_SUBJECT = "Ozymandias neustar data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = "File: " + FILE_NAME + \
                       " not found on S3 in cyber-intel/hancock/neustar! Neustar data is missing please view logs!"
EXCEPTION_SUBJECT = "Ozymandias monitor for Neustar data failed due to an exception!"
EXCEPTION_MESSAGE = "Ozymandias failed due to the following:\n\n{}\n\nPlease check the logs!"

# Watchman profile
TARGET = "Neustar"


class Ozymandias(Watchman):
    """
    Class of Ozymandias Watchman.
    """

    def __init__(self):
        pass

    def monitor(self):
        """
        Checks whether or not the neustar has a file added.
        @return: <Result> Result Object.
        """
        found_file, tb = self._check_file_exists()
        message = self._create_message(FILE_NAME, found_file, tb)
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
        parameters = parameter_chart.get(found_file)
        result = Result(success=parameters.get("success"),
                        disable_notifier=parameters.get("disable_notifier"),
                        state=parameters.get("state"),
                        subject=parameters.get("subject"),
                        message=message,
                        source=self.__class__.__name__,
                        target=TARGET,
                        )
        return result

    def _check_file_exists(self):
        """
        Checks if a file exists 2 days ago for Neustar data
        @return: <bool> whether or no that file exists
        @return: <str> traceback of exception.
        """
        try:
            found_file = validate_file_on_s3(BUCKET_NAME, FILE_PATH)
            return found_file, None
        except Exception as ex:
            LOGGER.exception(traceback.extract_stack())
            LOGGER.info('*' * 80)
            LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _create_result(self, success, state, subject, message):
        """
        Create the result object
        @param success: <bool> whether the file was found, false upon exception, otherwise false
        @param state: <str> state of the monitor check
        @param subject: <str> subject for the notification
        @param message: <str> content for the notification
        @return: <Result> result based on the parameters
        """
        result = Result(
            success=success,
            state=state,
            subject=subject,
            source=self.__class__.__name__,
            target=TARGET,
            message=message)
        return result

    def _create_message(self, is_status_valid, tb):
        """
        Depending on if the status of neustar file, send an email alert if it was not or an error occurred
        @param is_status_valid: whether or not the neustar file has good status or None if there was an exception
        @return: <str> the status of the check
        """
        FILE_STATUS = {
            None: {
                'message': EXCEPTION_MESSAGE.format(tb),
            },
            False: {
                'message': FAILURE_MESSAGE,
            },
            True: {
                'message': SUCCESS_MESSAGE,
            }
        }
        status = FILE_STATUS.get(is_status_valid)
        message = status.get('message')
        LOGGER.info(status.get('message'))
        return message
