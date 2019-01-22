"""
Created on January 22, 2019

This script monitors S3 ensuring data from the Georgia Tech Feed is properly transferred.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from datetime import datetime
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from utils.universal_watchmen import Watchmen
import pytz

LOGGER = getLogger("Spectre")
basicConfig(level=INFO)

#File Path Strings
BUCKET_NAME = "cyber-intel"
FILE_NAME = datetime.now().strftime('%Y') + "/" + datetime.now().strftime('%m') + "/gt_mpdns_" + \
            datetime.now().strftime("%Y%m%d") + ".zip"
FILE_PATH = "hancock/georgia_tech/" + FILE_NAME

#Message Strings
SUCCESS_MESSAGE = "Georgia Tech Feed data found on S3! File found: " + FILE_NAME
FAILURE_MESSAGE = "ERROR: " + FILE_NAME + " could not be found in hancock/georgia_tech! Please check S3 and Georgia Tech VM!"
FILE_NOT_FOUND_ERROR = "File: " + FILE_NAME + \
                       " not found on S3 in cyber-intel/hancock/georgia_tech! Georgia Tech data is missing, please view logs!"
EXCEPTION_MESSAGE = "Spectre monitor for Georgia Tech data failed due to an exception! Please check the logs!"


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
            #raise_alarm(SNS_TOPIC_ARN, FILE_NOT_FOUND_ERROR, FAIL_SUBJECT_MESSAGE)
    except Exception as ex:
        LOGGER.error(ex)
        LOGGER.info(EXCEPTION_MESSAGE)
        status = FAILURE_MESSAGE
        #raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, FAIL_SUBJECT_MESSAGE)

    print(status)
    #
    # LOGGER.info(status)
    # return status

if __name__ == '__main__':
    main(None, None)