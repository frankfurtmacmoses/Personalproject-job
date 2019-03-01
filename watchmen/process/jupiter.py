"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import json
from logging import getLogger, basicConfig, INFO

from watchmen.config import get_uint
from watchmen.config import settings
from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.endpoints import data as endpoints_data
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import get_content

LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

# Messages
CHECK_LOGS = "Please check logs for more details!"
ERROR_JUPITER = "Jupiter: Failure in runtime"
ERROR_SUBJECT = "Jupiter: Failure in checking endpoint"

MIN_ITEMS = get_uint('jupiter.min_items', 3)
NO_RESULTS = "There are no results! Endpoint file might be empty or Service Checker may not be working correctly. " \
             "Please check logs and endpoint file to help identify issue."
SUCCESS_MESSAGE = "All endpoints are good!"

SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:SockeyeTest")


def check_endpoints(endpoints):
    bad_list = []
    validated = []
    for item in endpoints:
        if item.get('path'):
            validated.append(item)
        else:
            bad_list.append(item)

    if bad_list:
        # raise_alam
        pass

    if len(validated) < MIN_ITEMS:
        # raise
        return None

    return validated


def load_endpoints():
    """
    Loads json file of endpoints.
    If an exception is thrown (meaning an error with opening and/or loading),
    an sns will be sent to the Sockeye Topic
    :return: the endpoints or exits upon exception
    """
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
        msg = fmt.format(fmt, bucket, data_file, data, ex)
        LOGGER.warning(msg)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=msg)

    endpoints = endpoints_data

    return endpoints


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    endpoints = load_endpoints()
    checker = ServiceChecker(endpoints)
    results = checker.start()
    validated_paths = checker.get_validated_paths()
    message = notify(results, endpoints, validated_paths)

    return message


def notify(results, endpoints, validated_paths):
    """
    Send notifications to Sockeye topic if failed endpoints exist or no results exist at all
    @param results: dict to be checked for failed endpoints
    @param endpoints: loaded endpoints data
    @param validated_paths: validated endpoints
    @return: the notification message
    """
    if not results or not isinstance(results, dict):
        # raise_alarm
        return

    failure = results.get('failure', [])
    success = results.get('success', [])

    # Checking failure list and announcing errors
    if failure and isinstance(failure, list):
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
        raise_alarm(SNS_TOPIC_ARN, subject=subject, message=message)
        return message

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
        raise_alarm(SNS_TOPIC_ARN, subject=ERROR_JUPITER, message=message)
        return message

    # All Successes
    return SUCCESS_MESSAGE


if __name__ == '__main__':
    main(None, None)