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
import types

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
SUCCESS_MESSAGE = "Sockeye endpoints are looking good!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:SockeyeTest"


def notify(results, endpoint_file):
    """
    Send notifications to Sockeye topic if failed endpoints exist or no results exist at all
    :param results: dict to be checked for failed endpoints
    :param endpoint_file: file name for notifications to know possible orirgn of some errors
    :return: the notification message
    """
    # Checking failure list and announcing errors
    if results['failure']:
        message = ""
        for failed in results['failure']:
            fail = "'{}' failed because of error '{}'. Check for empty file or dict.".format(failed['name'],
                                                                                             failed['_err'])
            LOGGER.error(fail)
            message += fail + '\n'
        message += CHECK_LOGS
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE)
        return message

    # Checking if results is empty
    if not results['failure'] and not results['success']:
        LOGGER.error("{} {}".format(NO_RESULTS, endpoint_file))
        message = "{} {}".format(NO_RESULTS_MESSAGE, endpoint_file)
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE)
        return message


def load_endpoints(endpoint_file):
    """
    Loads json file of endpoints.
    If an exception is thrown (meaning an error with opening and/or loading),
    an sns will be sent to the Sockeye Topic
    :param endpoint_file: the file to be opened
    :return: the endpoints or an exception
    """
    try:
        with open(endpoint_file) as data_file:
            points = json.load(data_file)
        return points
    except Exception as ex:
        LOGGER.error(ex)
        message = "ERROR: '{}'{}'{}'".format(endpoint_file, OPEN_FILE_ERROR, endpoint_file)
        LOGGER.info(message)
        raise_alarm(SNS_TOPIC_ARN, message, ERROR_MESSAGE + "\n\n" + str(ex))
        return message


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    local_endpoint_file = "endpoints.json"
    message = SUCCESS_MESSAGE
    # If a list is not returned, return the message string
    endpoints = load_endpoints(local_endpoint_file)
    if not isinstance(endpoints, types.ListType):
        return endpoints

    # Check Endpoints
    checked_points = ServiceChecker(endpoints)
    results = checked_points.start()

    # Checking endpoint results
    ep_message = notify(results, local_endpoint_file)
    if ep_message:
        return ep_message

    return message


if __name__ == '__main__':
    main(None, None)
