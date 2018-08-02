"""
Created on July 30, 2018

This script is designed to monitor hourly feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger, basicConfig, INFO
# Cyberint imports
from cyberint_watchmen.universal_watchmen import Watchmen
from cyberint_aws.sns_alerts import raise_alarm

LOGGER = getLogger("Manhattan")
basicConfig(level=INFO)

SUCCESS_MESSAGE = "HOURLY FEEDS ARE UP AND RUNNING NORMALLY!"
FAILURE_MESSAGE = "ONE OR MORE HOURLY FEEDS ARE FAILING, DOWN OR SUBMITTING ABNORMAL AMOUNTS OF DOMAINS!"
SUBJECT_MESSAGE = "Manhattan detected an issue with one or more of hourly feeds being down!"

SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"

ERROR_FEEDS = "FAILED/DOWNED FEEDS: "
ABNORMAL_SUBMISSIONS_MESSAGE = "ABNORMAL SUBMISSION AMOUNTS FROM THESE FEEDS: "

TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"
NOT_A_FEED_ERROR = "ERROR: Feed does not exist or is slotted in the wrong class!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"

FEEDS_TO_CHECK = {
    'bambenek_c2_ip': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 50, 'max': 300},
    'cox_feed': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 15000, 'max': 30000},
    'Xylitol_CyberCrime': {'metric_name': 'URI', 'min': 30, 'max': 50},
    'ecrimeX': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 10, 'max': 400},
    'G01Pack_DGA': {'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 15, 'max': 35},
    'tracker_h3x_eu': {'metric_name': 'URI', 'min': 5, 'max': 50},
    'Zeus_Tracker': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 35, 'max': 55}
}


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    watcher = Watchmen()
    status = SUCCESS_MESSAGE
    try:
        downed_feeds, submitted_out_of_range_feeds = watcher.process_feeds_metrics(FEEDS_TO_CHECK, TABLE_NAME)
        if downed_feeds or submitted_out_of_range_feeds:
            status = FAILURE_MESSAGE
            message = (
                    status + '\n' + ERROR_FEEDS + str(downed_feeds) + '\n' +
                    ABNORMAL_SUBMISSIONS_MESSAGE + str(submitted_out_of_range_feeds)
            )
            raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
    except Exception as ex:
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, SUBJECT_EXCEPTION_MESSAGE)
        status = FAILURE_MESSAGE
        LOGGER.error(ex)
    LOGGER.info(status)
    return status
