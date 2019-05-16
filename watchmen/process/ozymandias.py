"""
Created on June 19, 2018

This script is meant to monitor S3. This script will check that neustar has a file added daily
to ensure proper data flow. Runs once a day looking for these files.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com
"""
from datetime import datetime, timedelta
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.universal_watchmen import Watchmen
from watchmen.utils.logger import get_logger
from watchmen.config import settings
import pytz
import traceback

BUCKET_NAME = "cyber-intel"
FILE_NAME = (datetime.now(pytz.utc) - timedelta(days=2)).strftime("%Y%m%d").replace('/', '') + '.compressed'
FILE_PATH = "hancock/neustar/" + FILE_NAME
LOGGER = get_logger("Ozymandias", settings('logging.level', 'INFO'))
SNS_TOPIC_ARN = settings('ozymandias.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

SUCCESS_MESSAGE = "Neustar data found on S3! File found: " + FILE_NAME
FAILURE_MESSAGE = "ERROR: " + FILE_NAME + " could not be found in hancock/neustar! Please check S3 and neustar VM!"
FAIL_SUBJECT_MESSAGE = "Ozymandias neustar data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = "File: " + FILE_NAME + \
                       " not found on S3 in cyber-intel/hancock/neustar! Neustar data is missing please view logs!"
EXCEPTION_MESSAGE = "Ozymandias monitor for Neustar data failed due to an exception!"
EXCEPTION_BODY_MESSAGE = "Ozymandias failed due to the following:\n\n{}\n\nPlease check the logs!"


def check_file_exists():
    """
    Checks if a file exists 2 days ago for Neustar data
    @return: whether or no that file exists
    """
    watcher = Watchmen(bucket_name=BUCKET_NAME)

    try:
        found_file = watcher.validate_file_on_s3(FILE_PATH)
        return found_file
    except Exception as ex:
        LOGGER.error(ex)
        trace = traceback.format_exc(ex)
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_BODY_MESSAGE.format(trace), EXCEPTION_MESSAGE)
        return None


# pylint: disable=unused-argument
def main(event, context):
    """
    Checks that neustar has a file added daily
    :return: whether or not that daily file exists
    """
    file_exists = check_file_exists()
    status = notify(file_exists)

    LOGGER.info(status)
    return status


def notify(file_exists):
    """
    Depending on the existence of the checked file, send an email alert upon failure or exception
    @param file_exists: state of the file
    @return: message signifying the current state of the check
    """
    if file_exists is None:
        LOGGER.info(EXCEPTION_MESSAGE)
        return EXCEPTION_MESSAGE

    if not file_exists:
        LOGGER.info(FILE_NOT_FOUND_ERROR)
        raise_alarm(SNS_TOPIC_ARN, FILE_NOT_FOUND_ERROR, FAIL_SUBJECT_MESSAGE)
        return FAILURE_MESSAGE

    return SUCCESS_MESSAGE
