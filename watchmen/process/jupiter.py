"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import json
import pytz

from datetime import datetime
from watchmen.config import get_boolean
from watchmen.config import get_uint
from watchmen.config import settings
from watchmen.common.cal import InfobloxCalendar
from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.endpoints import DATA as ENDPOINTS_DATA
from watchmen.utils.logger import get_logger
# from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import copy_contents_to_bucket
from watchmen.utils.s3 import get_content
# from watchmen.utils.s3 import mv_key

LOGGER = get_logger("Jupiter", settings('logging.level'))

CHECK_TIME_UTC = datetime.utcnow()
CHECK_TIME_PDT = pytz.utc.localize(CHECK_TIME_UTC).astimezone(pytz.timezone('US/Pacific'))
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
MIN_ITEMS = get_uint('jupiter.min_items', 1)
SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

# S3
S3_BUCKET = settings('aws.s3.bucket')
S3_PREFIX = settings('aws.s3.prefix')
S3_PREFIX_JUPITER = settings('jupiter.s3_prefix')
S3_PREFIX_STATE = '{}/{}/LATEST'.format(S3_PREFIX, S3_PREFIX_JUPITER)

# Messages
CHECK_LOGS = "Please check logs for more details!"
ERROR_JUPITER = "Jupiter: Failure in runtime"
ERROR_SUBJECT = "Jupiter: Failure in checking endpoint"
NO_RESULTS = "There are no results! Endpoint file might be empty or Service Checker may not be working correctly. " \
             "Please check logs and endpoint file to help identify the issue."
NOT_ENOUGH_EPS = "Jupiter: Too Few Endpoints"
NOT_ENOUGH_EPS_MESSAGE = "Endpoint count is below minimum. There is no need to check or something is wrong with " \
                         "endpoint file."
RESULTS_DNE = "Results do not exist! There is nothing to check. Service Checker may not be working correctly. " \
              "Please check logs and endpoint file to help identify the issue."
SKIP_MESSAGE_FORMAT = "Notification is skipped at {}"
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
        # raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        pass

    if len(validated) < MIN_ITEMS:
        subject = NOT_ENOUGH_EPS
        message = NOT_ENOUGH_EPS_MESSAGE
        LOGGER.warning(NOT_ENOUGH_EPS_MESSAGE)
        # raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        return None

    return validated


def _check_last_failure():
    """
    Use key, e.g. bucket/prefix/LATEST to check if last check failed.
    LATEST key contains result (non-empty) if last result has failure; empty indicates success.

    @return: True if last check failed; otherwise, False.
    """
    data = ''
    # data = get_content(S3_PREFIX_STATE, bucket=S3_BUCKET)
    return data != '' and data is not None


def _check_skip_notification():
    """
    If current day and hour do not fall under the desired notification times, there is no need to send a notification
    @return: whether or not to send a notification
    """
    now = CHECK_TIME_PDT
    hour = now.hour
    year = now.year
    # Create a calendar for last year, current year, and next year
    cal = InfobloxCalendar(year - 1, year + 1)
    to_skip = False
    if not cal.is_workday():
        to_skip = hour % 8 != 0
    elif not cal.is_workhour(hour):
        to_skip = hour % 4 != 0

    LOGGER.debug("The current hour is %s and to_skip = %s", hour, to_skip)

    return to_skip


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

    data = get_content(key_name=data_file, bucket=bucket)
    try:
        LOGGER.info("The contents of data: \n{}".format(data))
        endpoints = json.loads(data)
        if endpoints and isinstance(endpoints, list):
            validated = check_endpoints(endpoints)
            if validated:
                return validated
    except Exception as ex:
        LOGGER.info("Inside Exception Block")
        subject = "Jupiter endpoints - load error"
        fmt = "Cannot load endpoints from bucket={}, key={}\n{}\nException:{}"
        msg = fmt.format(bucket, data_file, data, ex)
        LOGGER.warning(msg)
        LOGGER.info("About to send alarm")
        # raise_alarm(topic_arn=SNS_TOPIC_ARN, subject=subject, msg=msg)
        LOGGER.info("Alarm sent")
    endpoints = ENDPOINTS_DATA
    LOGGER.info("The contents of endpoints: \n{}".format(endpoints))

    return endpoints


def log_result(results):
    """
    Log results to s3
    @param results: to be logged
    """
    try:
        prefix_datetime = CHECK_TIME_UTC.strftime(DATETIME_FORMAT)
        prefix_result = '{}/{}/{}/{}'.format(S3_PREFIX, S3_PREFIX_JUPITER, CHECK_TIME_UTC.year, prefix_datetime)
        LOGGER.info("Jupiter Watchmen results:\n{}".format(results))
        # save result to s3
        content = json.dumps(results, indent=4, sort_keys=True)
        # copy_contents_to_bucket(content, prefix_result, S3_BUCKET)
        LOGGER.debug("Skipped S3 content dump in log result")
    except Exception as ex:
        LOGGER.error(ex)
    return prefix_result


def log_state(summarized_result, prefix):
    """
    Logs whether the current state of Jupiter contains failed endpoints or all are successes.
    If there are failures, they will be written to the LATEST file on s3.
    An empty LATEST file indicates that there are no failures.
    Each time this method is run, it will overwrite the contents of LATEST.
    @param summarized_result: dictionary containing results of the sanitization of the successful and failed endpoints.
    @param prefix: prefix of the original file
    """
    try:
        success = summarized_result.get('success')
        content = '' if success else json.dumps(summarized_result, indent=4, sort_keys=True)
        prefix_state = '{}/{}/LATEST'.format(S3_PREFIX, S3_PREFIX_JUPITER)
        LOGGER.debug("Skipped S3 content dump in log state")
        # copy_contents_to_bucket(content, prefix_state, S3_BUCKET)
        state = 'SUCCESS' if success else 'FAILURE'
        # mv_key(prefix, '{}_{}.json'.format(prefix, state), bucket=S3_BUCKET)
    except Exception as ex:
        LOGGER.error(ex)


# pylint: disable=unused-argument
def main(event, context):
    """
    Health check all the endpoints from endpoints.json
    :return: results from checking Sockeye endpoints
    """
    endpoints = load_endpoints()
    LOGGER.debug("DONE: Loaded Endpoints")

    checked_endpoints = check_endpoints(endpoints)
    LOGGER.debug("DONE: Checked Endpoints")

    checker = ServiceChecker(checked_endpoints)
    LOGGER.debug("DONE: Endpoints went through ServiceChecker")

    results = checker.start()
    LOGGER.debug("DONE: Checked Endpoint Routes and got results")

    prefix = log_result(results)
    LOGGER.debug("DONE: Logged Results")

    validated_paths = checker.get_validated_paths()
    LOGGER.debug("DONE: Validated All Paths")

    summarized_result = summarize(results, endpoints, validated_paths)
    LOGGER.debug("DONE: Summarized Results")

    log_state(summarized_result, prefix)
    LOGGER.debug("DONE: Logged State")

    status = notify(summarized_result)
    LOGGER.debug("DONE: COMPLETED")

    return status
    # _update_endpoints()


def notify(summarized_result):
    """
    Send notifications to Sockeye topic if failed endpoints exist or no results exist at all.
    Notifications vary depending on the time and day.
    If the day is a holiday and the hour is 8am or 4pm, a notification will be sent.
    If the day is a work day and the hour is 8am, 12pm, or 4pm, a notification will be sent.
    Otherwise, all notifications will be skipped.
    @param summarized_result: dictionary containing notification information
    @return: the status of the endpoints: success, failures, or skipped
    """
    message = summarized_result.get('message')
    subject = summarized_result.get('subject')
    success = summarized_result.get('success')

    if success:
        return SUCCESS_MESSAGE

    enable_calendar = get_boolean('jupiter.enable_calendar')
    # Skip if last check in state file is not a failure and it is not time to send a notification
    last_failed = summarized_result.get('last_failed')
    is_skipping = enable_calendar and last_failed and _check_skip_notification()
    if is_skipping:
        return SKIP_MESSAGE_FORMAT.format(CHECK_TIME_UTC)

    # raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
    return "FAILURES occurred! Check the logs for more details!"


def summarize(results, endpoints, validated_paths):
    """
    Creates a dictionary based on endpoints results.
    This dictionary will be given to notify to create alarm messages and logs.
    @param results: dict to be checked for failed endpoints
    @param endpoints: loaded endpoints data
    @param validated_paths: validated endpoints
    @return: the notification message
    """
    last_failed = _check_last_failure()

    if not results or not isinstance(results, dict):
        message = RESULTS_DNE
        return {
            "last_failed": last_failed,
            "message": message,
            "subject": ERROR_JUPITER,
            "success": False,
        }

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
        return {
            "last_failed": last_failed,
            "message": message,
            "subject": ERROR_JUPITER,
            "success": False,
        }

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
        return {
            "last_failed": last_failed,
            "message": message,
            "subject": subject,
            "success": False,
        }

    # All Successes
    return {
        "message": SUCCESS_MESSAGE,
        "success": True,
    }


def _update_endpoints():
    content = json.dumps(ENDPOINTS_DATA, indent=4, sort_keys=True)
    key = '{}/{}/endpoints.json'.format(S3_PREFIX, S3_PREFIX_JUPITER)
    copy_contents_to_bucket(content, key, S3_BUCKET)


if __name__ == "__main__":
    main(None, None)
