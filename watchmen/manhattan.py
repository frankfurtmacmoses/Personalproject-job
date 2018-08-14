"""
Created on July 30, 2018

This script is designed to monitor daily, hourly, and weekly feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger, basicConfig, INFO
from time import time
# Cyberint imports
from watchmen.utils.universal_watchmen import Watchmen
from cyberint_aws.sns_alerts import raise_alarm

LOGGER = getLogger("Manhattan")
basicConfig(level=INFO)

DAILY = "Daily"
HOURLY = "Hourly"
WEEKLY = "Weekly"

HOUR_IN_MILI = 360000
DAY_IN_MILI = 86400000
FOUR_DAYS_IN_MILI = 345600000

SUCCESS_MESSAGE = "feeds are up and running normally!"
FAILURE_MESSAGE = "One or more feeds are down or submitting abnormal amounts of domains!"
SUBJECT_MESSAGE = "Manhattan detected an issue with one or more feeds being down!"

SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"

ERROR_FEEDS = "Downed feeds: "
ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "

TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"
NOT_A_FEED_ERROR = "ERROR: Feed does not exist or added in the wrong module!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"
LOG_GROUP_NAME = 'feed-eaters-prod'

FEEDS_TO_CHECK_HOURLY = {
    'bambenek_c2_ip': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 50, 'max': 300},
    'cox_feed': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 15000, 'max': 35000},
    'Xylitol_CyberCrime': {'metric_name': 'URI', 'min': 30, 'max': 50},
    'ecrimeX': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 10, 'max': 400},
    'G01Pack_DGA': {'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 15, 'max': 35},
    'tracker_h3x_eu': {'metric_name': 'URI', 'min': 5, 'max': 50},
    'VX_Vault': {'metric_name': 'URI', 'min': 1, 'max': 20},
    'Ransomware_tracker': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 1, 'max': 15},
    'Zeus_Tracker': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 35, 'max': 55}
}

FEEDS_HOURLY_NAMES = [
                      'bambenek-ip-scraper', 'cox-feed', 'cybercrime-scraper', 'ecrimex-scraper',
                      'g01-dga', 'tracker-h3x-eu-scraper', 'vxvault-scraper', 'ransomware-tracker-scraper',
                      'zeus-tracker-scraper'
]

FEEDS_TO_CHECK_DAILY = {
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

FEEDS_DAILY_NAMES = [
                     'feodo-scraper', 'ff-goz-dga', 'locky-dga-scraper', 'malc0de-scraper',
                     'tor-exit-node-scraper'
]


# IMPORTANT NOTE: This has to run on Friday in order to ensure proper date traversal!
# How it works:
#               Monday: 4
#               Tuesday: 3
#               Wednesday: 2
#               Thursday: 1
#               Friday: 0
#               To check for monday you subtract 4 days from the run day on Friday.
#               IE If the date is 08/10/2018 and I want to check feeds running on Monday
#                  then I subtract 4 days to 08/06/2018 and check the dynamodb metrics table.
FEEDS_TO_CHECK_WEEKLY = {
    'c_APT_ure': {'metric_name': 'FQDN', 'min': 250, 'max': 450, 'hour_submitted': '09', 'days_to_subtract': 4}
}

FEEDS_WEEKLY_NAMES = [
                      'ponmocup-scraper'
]


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    watcher = Watchmen(log_group_name=LOG_GROUP_NAME)
    status = SUCCESS_MESSAGE
    downed_feeds = []
    submitted_out_of_range_feeds = []
    event_type = event.get('type')
    try:
        end = int(time() * 1000)
        if event_type == HOURLY:
            start = end - HOUR_IN_MILI
            downed_feeds = watcher.process_feeds_logs(FEEDS_HOURLY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_HOURLY, TABLE_NAME, 0
            )
        elif event_type == DAILY:
            start = end - DAY_IN_MILI
            downed_feeds = watcher.process_feeds_logs(FEEDS_DAILY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_DAILY, TABLE_NAME, 1
            )
        elif event_type == WEEKLY:
            start = end - FOUR_DAYS_IN_MILI
            downed_feeds = watcher.process_feeds_logs(FEEDS_WEEKLY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_WEEKLY, TABLE_NAME, 2
            )
    except Exception as ex:
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE, SUBJECT_EXCEPTION_MESSAGE)
        status = FAILURE_MESSAGE
        LOGGER.error(ex)

    if downed_feeds or submitted_out_of_range_feeds:
        status = FAILURE_MESSAGE
        message = (
                event_type + ": " + status + '\n' + ERROR_FEEDS + str(downed_feeds) + '\n' +
                ABNORMAL_SUBMISSIONS_MESSAGE + str(submitted_out_of_range_feeds)
        )
        LOGGER.info(message)
        raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
    LOGGER.info(event_type + ": " + status)
    return status
