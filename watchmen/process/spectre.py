"""
Created on January 22, 2019

This script monitors S3 ensuring data from Georgia Tech Feed is properly transferred.
If data is not found or has a value of 0, an alert is sent out.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import traceback
from datetime import datetime, timedelta
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.logger import get_logger
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.config import settings
import pytz

LOGGER = get_logger("Spectre", settings('logging.level', 'INFO'))

# Filepath Strings
BUCKET_NAME = "cyber-intel"
PATH_TO_FILES = "hancock/georgia_tech/"
SNS_TOPIC_ARN = settings('spectre.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

# Message Strings
SUCCESS_MESSAGE = "Georgia Tech Feed data found on S3! File found: "
FAILURE_MESSAGE = "could not be found in hancock/georgia_tech! Please check S3 and Georgia Tech logs!"
FAIL_SUBJECT_MESSAGE = "Spectre Georgia Tech data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = " not found on S3 in cyber-intel/hancock/georgia_tech! Georgia Tech data is missing, " \
                       "please view the logs!"
EXCEPTION_MESSAGE = "Spectre monitor for Georgia Tech data failed due to an exception!"
EXCEPTION_BODY_MESSAGE = "Spectre failed due to the following:\n\n{}\n\nPlease check the logs!"


def check_if_found_file(filename):
    """
    Check if the file for yesterday is found on the Georgia Tech feed
    @param filename: name of the file to check
    @return: whether or not the file was found; otherwise, None upon exception
    """
    file_path = '{}{}'.format(PATH_TO_FILES, filename)

    try:
        found_file = validate_file_on_s3(BUCKET_NAME, file_path)
        return found_file
    except Exception as ex:
        LOGGER.exception(traceback.extract_stack())
        LOGGER.info('*' * 80)
        LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
        return None


def get_s3_filename():
    """
    Gets yesterday's s3 filename
    :return: filename
    """
    now = datetime.now(pytz.utc)
    yesterday = now - timedelta(days=1)
    filename = yesterday.strftime('%Y') + "/" + yesterday.strftime('%m') + \
        "/gt_mpdns_" + yesterday.strftime("%Y%m%d") + ".zip"
    return filename


# pylint: disable=unused-argument
def main(event, context):
    """
    Checks that Georgia Tech adds a file daily
    :return: Whether or not that file exists
    """
    filename = get_s3_filename()
    file_found = check_if_found_file(filename)
    message = notify(file_found, filename)

    LOGGER.info(message)
    return message


def notify(file_found, filename):
    """
    Depending if the file was found or not, send an email alert if it was not or an error occurred
    @param file_found: whether or not the file was found (boolean) or None if there was an exception
    @param filename: name of the file that was checked (used for notification purposes)
    @return: the status of the check
    """
    if file_found is None:
        LOGGER.info(EXCEPTION_MESSAGE)
        message = 'ERROR: {}-{}'.format(EXCEPTION_MESSAGE, filename)
        return message

    if not file_found:
        LOGGER.info('File: {}{}'.format(filename, FILE_NOT_FOUND_ERROR))
        message = 'ERROR: {}{}'.format(filename, FAILURE_MESSAGE)
        raise_alarm(SNS_TOPIC_ARN, 'File: {}{}'.format(filename, FILE_NOT_FOUND_ERROR), FAIL_SUBJECT_MESSAGE)
        return message

    return SUCCESS_MESSAGE
