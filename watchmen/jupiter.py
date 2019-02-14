"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
from logging import getLogger, basicConfig, INFO
from utils.sns_alerts import raise_alarm
from common.svc_checker import ServiceChecker
import json

LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# Messages
CHECK_LOGS = "Please check logs for more details!"
ERROR_MESSAGE = "There is an error with the Sockeye endpoints!"
FOUND_FAILURES = "Endpoints Failed!"
NO_RESULTS = "There are no results! Endpoint file might be empty. Please check logs and "
NO_RESULTS_MESSAGE = "No endpoints were checked! The results from the service check is empty! Please check the logs and"
OPEN_FILE_ERROR = " could not be opened and caused an exception. There might be a typo or format error in the file or" \
                  " it may be empty. Please check the logs and "

ENDPOINT_FILE = "endpoints.json"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:Sockeye0"

# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    message = "Sockeye endpoints are looking good!"
    # Checking if endpoint file can be opened
    try:
        with open(ENDPOINT_FILE) as data_file:
            points = json.load(data_file)
    except Exception as ex:
        LOGGER.error(ex)
        message = "ERROR: '{}'{}'{}'".format(ENDPOINT_FILE, OPEN_FILE_ERROR, ENDPOINT_FILE)
        LOGGER.info(message)
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE + "\n\n" + str(ex))
        return message

    ep = ServiceChecker(points)
    results = ep.start()

    # Checking endpoint results
    # Checking failure list and announcing errors
    if results['failure']:
        message = ""
        for failed in results['failure']:
            fail = "'{}' failed because of error '{}'. Check for empty file or dict.".format(failed['name'], failed['_err'])
            LOGGER.error(fail)
            message += fail + '\n'
        message += CHECK_LOGS
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE)
        return message

    # Checking if results is empty
    if not results['failure'] and not results['success']:
        LOGGER.error("{} {}".format(NO_RESULTS, ENDPOINT_FILE))
        message = "{} {}".format(NO_RESULTS_MESSAGE, ENDPOINT_FILE)
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE)
        return message

    return message


if __name__ == '__main__':
    main(None, None)
