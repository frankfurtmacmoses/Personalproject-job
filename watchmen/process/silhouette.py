"""
Created on July 18, 2018

This script is designed to check the lookalike feed daily and
ensure that data is coming through into S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

"""

# Python imports
from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
import pytz
import json

# Cyberint imports
from watchmen.utils.universal_watchmen import Watchmen
from watchmen.utils.sns_alerts import raise_alarm

LOGGER = getLogger("Silhouette")
basicConfig(level=INFO)

SUCCESS_MESSAGE = "Lookalike feed is up and running!"
FAILURE_MESSAGE = "ERROR: Lookalike feed never added files from 2 days ago! " \
                  "The feed may be down or simply did not complete!"
FAILURE_SUBJECT = "Silhouette watchmen detected an issue with lookalike feed!"
SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-lookalike-s3"

EXCEPTION_MESSAGE = "Silhouette watchmen for the lookalike feed failed due to an exception! Please check the logs!"

COMPLETED_STATUS = "COMPLETED"

BUCKET_NAME = "cyber-intel"
FILE_PATH = "analytics/lookalike/prod/results/"
STATUS_FILE = "status.json"


def check_process_status():
    """
    Checks the status of the process check
    @return: whether or not the process succeeded; otherwise, None upon exception
    """
    try:
        is_status_valid = process_status()
        return is_status_valid
    except Exception as ex:
        LOGGER.error(ex)
        return None


# pylint: disable=unused-argument
def main(event, context):
    """
    main
    :return: status of whether lookalike feed working or not
    """
    is_status_valid = check_process_status()
    status = notify(is_status_valid)

    LOGGER.info(status)
    return status


def process_status():
    """
    Checks timestamp of previous day for lookalike feed files being dropped into
    S3. Status.json has a state which determines if the process was successful or not.
    :return: whether the process finished or not
    """
    watcher = Watchmen(BUCKET_NAME)
    is_completed = False
    check_time = (datetime.now(pytz.utc) - timedelta(days=2)).strftime("%Y %m %d").split(' ')
    key = FILE_PATH + check_time[0] + '/' + check_time[1] + '/' + check_time[2] + '/' + STATUS_FILE
    file_contents = watcher.get_file_contents_s3(key)
    if file_contents:
        status_json = json.loads(file_contents)
        if status_json.get('STATE') == COMPLETED_STATUS:
            is_completed = True
    return is_completed


def notify(is_status_valid):
    """
    Send a notification alert upon failure
    @param is_status_valid: the status of the check determining the notification status
    @return: the notification status of the check
    """
    if is_status_valid is None:
        status = EXCEPTION_MESSAGE
        raise_alarm(SNS_TOPIC_ARN, status, FAILURE_SUBJECT)
        return status

    if not is_status_valid:
        status = FAILURE_MESSAGE
        raise_alarm(SNS_TOPIC_ARN, status, FAILURE_SUBJECT)
        return status

    return SUCCESS_MESSAGE
