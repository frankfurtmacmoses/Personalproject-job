"""
Created on June 19, 2018

This script is meant to monitor S3. This script will check that neustar has a file added daily
to ensure proper data flow. Runs once a day looking for these files.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com
"""

from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from utils.universal_watchmen import Watchmen
import pytz

LOGGER = getLogger("ManhattanWeekly")
basicConfig(level=INFO)

FILE_NAME = (datetime.now(pytz.utc) - timedelta(days=2)).strftime("%Y%m%d").replace('/', '') + '.compressed'

SUCCESS_MESSAGE = "Neustar data found on S3! File found: " + FILE_NAME
FAILURE_MESSAGE = "ERROR: " + FILE_NAME + " could not be found in hancock/neustar! Please check S3 and neustar VM!"
FAIL_SUBJECT_MESSAGE = "Ozymandias neustar data monitor detected a failure!"
FILE_NOT_FOUND_ERROR = "File: " + FILE_NAME + \
                       " not found on S3 in cyber-intel/hancock/neustar! Neustar data is missing please view logs!"
EXCEPTION_MESSAGE = "Ozymandias monitor for Neustar data failed due to an exception! Please check the logs!"
BUCKET_NAME = "cyber-intel"
FILE_PATH = "hancock/neustar/" + FILE_NAME
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:Hancock"


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of the file
    """
    watcher = Watchmen(bucket_name=BUCKET_NAME)
    status = SUCCESS_MESSAGE
    try:
        found_file = watcher.validate_file_on_s3(FILE_PATH)
        if not found_file:
            LOGGER.info(FILE_NOT_FOUND_ERROR)
            status = FAILURE_MESSAGE
            raise_alarm(SNS_TOPIC_ARN, FILE_NOT_FOUND_ERROR, FAIL_SUBJECT_MESSAGE)
    except Exception as ex:
        LOGGER.error(ex)
        LOGGER.info(EXCEPTION_MESSAGE)
        status = FAILURE_MESSAGE
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, FAIL_SUBJECT_MESSAGE)

    LOGGER.info(status)
    return status
