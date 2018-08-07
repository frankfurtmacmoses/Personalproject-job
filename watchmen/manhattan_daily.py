"""
Created on August 4, 2018

This script is designed to monitor daily feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger, basicConfig, INFO
# Cyberint imports
from cyberint_watchmen.universal_watchmen import Watchmen
from cyberint_aws.sns_alerts import raise_alarm

LOGGER = getLogger("ManhattanDaily")
basicConfig(level=INFO)

SUCCESS_MESSAGE = "Daily feeds are up and running normally!"
FAILURE_MESSAGE = "One or more daily feeds are down or submitting abnormal amounts of domains!"
SUBJECT_MESSAGE = "Manhattan detected an issue with one or more of daily feeds being down!"

SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"

ERROR_FEEDS = "Failed/Downed feeds: "
ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "

TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"
NOT_A_FEED_ERROR = "ERROR: Feed does not exist or is slotted in the wrong module!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"

FEEDS_TO_CHECK = {
    'CryptoLocker_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 2500, 'max': 4500, 'hour_submitted': '09'
    },
    'feodo_tracker': {
        'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 5, 'max': 35, 'hour_submitted': '21'
    },
    'FastFlux_GameoverZeus_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 10000, 'max': 12000, 'hour_submitted': '10'
    },
    'TI_Locky_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 20000, 'max': 30000, 'hour_submitted': '10'
    },
    'MALC0DE': {
        'metric_name': 'URI_TIDE_SUCCESS', 'min': 300, 'max': 700, 'hour_submitted': '07'
    },
    'torstatus.blutmagie.de': {
        'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 500, 'max': 1500, 'hour_submitted': '10'
    }
}


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all daily feeds
    """
    watcher = Watchmen()
    status = SUCCESS_MESSAGE
    try:
        downed_feeds, submitted_out_of_range_feeds = watcher.process_feeds_metrics(FEEDS_TO_CHECK, TABLE_NAME, 1)
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
