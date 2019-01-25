"""
Created on January 22, 2019

This script monitors S3 ensuring data from Georgia Tech Feed is properly transferred.
If data is not found or has a value of 0, an alert is sent out.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from utils.universal_watchmen import Watchmen
import pytz

LOGGER = getLogger("Spectre")
basicConfig(level=INFO)

# Filepath Strings
BUCKET_NAME = "cyber-intel"
PATH_TO_FILES = "hancock/georgia_tech/"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:Hancock"

# Message Strings
SUCCESS_MESSAGE = "Georgia Tech Feed data found on S3! File found: "
FAILURE_MESSAGE = "could not be found in hancock/georgia_tech! Please check S3 and Georgia Tech logs!"
FAIL_SUBJECT_MESSAGE = "Spectre Georgia Tech data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = " not found on S3 in cyber-intel/hancock/georgia_tech! Georgia Tech data is missing, " \
                       "please view the logs!"
EXCEPTION_MESSAGE = "Spectre monitor for Georgia Tech data failed due to an exception! Please check the logs!"


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of the file
    """
    watcher = Watchmen(bucket_name=BUCKET_NAME)
    fn = get_s3_filename()
    file_path = '{}{}'.format(PATH_TO_FILES, fn)
    message = '{}{}'.format(SUCCESS_MESSAGE, fn)
    try:
        found_file = watcher.validate_file_on_s3(file_path)
        if not found_file:
            LOGGER.info('File: {}{}'.format(fn, FILE_NOT_FOUND_ERROR))
            message = 'ERROR: {}{}'.format(fn, FAILURE_MESSAGE)
            raise_alarm(SNS_TOPIC_ARN, 'File: {}{}'.format(fn, FILE_NOT_FOUND_ERROR), FAIL_SUBJECT_MESSAGE)
    except Exception as ex:
        LOGGER.error(ex)
        LOGGER.info(EXCEPTION_MESSAGE)
        message = 'ERROR: {}{}'.format(fn, FAILURE_MESSAGE)
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, FAIL_SUBJECT_MESSAGE)

    LOGGER.info(message)
    return message


def get_s3_filename():
    """
    Gets yesterday's s3 filename
    :return: filename
    """
    now = datetime.now(pytz.utc)
    yesterday = now - timedelta(days=1)
    fn = yesterday.strftime('%Y') + "/" + yesterday.strftime('%m') + "/gt_mpdns_" + yesterday.strftime("%Y%m%d") + ".zip"
    return fn
