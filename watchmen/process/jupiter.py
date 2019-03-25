"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import json
from datetime import datetime
from logging import getLogger, basicConfig, INFO

from watchmen.config import get_uint
from watchmen.config import settings
from watchmen.common.cal import InfobloxCalendar
from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.endpoints import DATA as ENDPOINTS_DATA
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import get_content

LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# Messages
CHECK_LOGS = "Please check logs for more details!"
ERROR_JUPITER = "Jupiter: Failure in runtime"
ERROR_SUBJECT = "Jupiter: Failure in checking endpoint"
MIN_ITEMS = get_uint('jupiter.min_items', 1)
NO_RESULTS = "There are no results! Endpoint file might be empty or Service Checker may not be working correctly. " \
             "Please check logs and endpoint file to help identify the issue."
NOT_ENOUGH_EPS = "Jupiter: Too Few Endpoints"
NOT_ENOUGH_EPS_MESSAGE = "Endpoint count is below minimum. There is no need to check or something is wrong with " \
                         "endpoint file."
RESULTS_DNE = "Results do not exist! There is nothing to check. Service Checker may not be working correctly. " \
              "Please check logs and endpoint file to help identify the issue."
SKIP_MESSAGE_FORMAT = "Notification is skipped at {}"
SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:Sockeye")
SUCCESS_MESSAGE = "All endpoints are good!"


def check_endpoints(endpoints):
    """
    Checks if first level endpoints are valid or not.
    Non-valid endpoints are printed with error messages.
    If too few validated endpoints exist, no need to check.
    @param endpoints: endpoints to be checked
    @return: list of validated endpoints
    """
    bad_list = []
    validated = []
    for item in endpoints:
        if item.get('path'):
            validated.append(item)
        else:
            bad_list.append(item)

    if bad_list:
        subject = ERROR_SUBJECT
        messages = []
        for item in bad_list:
            msg = 'There is not a path to check for: {}'.format(item.get('name', "There is not a name available"))
            messages.append(msg)
            LOGGER.error('Notify failure:\n%s', msg)
        message = '\n'.join(messages)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        pass

    if len(validated) < MIN_ITEMS:
        subject = NOT_ENOUGH_EPS
        message = NOT_ENOUGH_EPS_MESSAGE
        LOGGER.warning(NOT_ENOUGH_EPS_MESSAGE)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        return None

    return validated


def _check_skip_notification():
    """
    If current day and hour do not fall under the desired notification times, there is not need to send a notification
    @return: whether or not to send a notification
    """
    now = datetime.now()
    hour = now.hour
    year = now.year
    # Create a calendar for last yera, current year, and next year
    cal = InfobloxCalendar(year - 1, year, year + 1)
    to_skip = False

    if not cal.is_workday():
        to_skip = hour % 8 != 0
    elif not cal.is_workhour(hour):
        to_skip = hour % 4 != 0

    return to_skip


def load_endpoints():
    """
    Loads json file of endpoints.
    If an exception is thrown (meaning an error with opening and/or loading),
    an sns will be sent to the Sockeye Topic
    :return: the endpoints or exits upon exception
    """
    # This will always run because there is no s3 file setup yet
    data_path = settings("aws.s3.prefix")
    data_file = settings("jupiter.endpoints")

    if data_path:
        data_file = '{}/{}'.format(data_path, data_file)

    bucket = settings("aws.s3.bucket")
    data = get_content(data_file, bucket=bucket)

    try:
        endpoints = json.loads(data)
        if endpoints and isinstance(endpoints, list):
            validated = check_endpoints(endpoints)
            if validated:
                return validated
    except Exception as ex:
        subject = "Jupiter endpoints - load error"
        fmt = "Cannot load endpoints from bucket={}, key={}\n{}\nException:{}"
        msg = fmt.format(bucket, data_file, data, ex)
        LOGGER.warning(msg)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=msg)

    endpoints = ENDPOINTS_DATA

    return endpoints


def log_result(results):
    """
    Log results to s3
    @param results: to be logged
    @return:
    """
    LOGGER.info("The results are:\n{}".format(results))
    # save result to s3
    pass


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    endpoints = load_endpoints()
    checked_endpoints = check_endpoints(endpoints)
    checker = ServiceChecker(checked_endpoints)
    results = checker.start()
    validated_paths = checker.get_validated_paths()
    message = notify(results, endpoints, validated_paths)

    return message


def notify(results, endpoints, validated_paths):
    """
    Send notifications to Sockeye topic if failed endpoints exist or no results exist at all.
    Notifications vary depending on the time and day.
    If the day is a holiday and the hour is 8am or 4pm, a notification will be sent.
    If the day is a work day and the hour is 8am, 12pm, or 4pm, a notification will be sent.
    Otherwise, all notifications will be skipped.
    Although a notification may not be sent, results will be logged at all times.
    @param results: dict to be checked for failed endpoints
    @param endpoints: loaded endpoints data
    @param validated_paths: validated endpoints
    @return: the notification message
    """
    if not results or not isinstance(results, dict):
        message = RESULTS_DNE
        raise_alarm(SNS_TOPIC_ARN, subject=ERROR_JUPITER, msg=message)
        return message

    log_result(results)

    failure = results.get('failure', [])
    success = results.get('success', [])

    # Checking if results is empty
    if not failure and not success:
        split_line = '-'*80
        message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(results, sort_keys=True, indent=2),
            split_line,
            json.dumps(endpoints, indent=2),
            split_line,
            json.dumps(validated_paths, indent=2)
        )
        LOGGER.error(message)
        message = "{}\n\n\n{}".format(message, NO_RESULTS)
        raise_alarm(SNS_TOPIC_ARN, subject=ERROR_JUPITER, msg=message)
        return message

    # Checking failure list and announcing errors
    if failure and isinstance(failure, list):
        if _check_skip_notification():
            return SKIP_MESSAGE_FORMAT.format(datetime.now())

        messages = []
        for item in failure:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            messages.append(msg)
            LOGGER.error('Notify failure:\n%s', msg)
        message = '{}\n\n\n{}'.format('\n\n'.join(messages), CHECK_LOGS)

        first_failure = 's' if len(failure) > 1 else ' - {}'.format(failure[0].get('name'))
        subject = '{}{}'.format(ERROR_SUBJECT, first_failure)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        return message

    # All Successes
    return SUCCESS_MESSAGE
