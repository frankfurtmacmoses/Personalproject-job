"""
Created on July 30, 2018

This script is designed to monitor daily, hourly, and weekly feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
import traceback
from datetime import datetime, timedelta
import pytz
# Watchmen imports
from watchmen.utils.universal_watchmen import Watchmen
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.logger import get_logger
from watchmen.config import settings

LOGGER = get_logger("Manhattan", settings('logging.level', 'INFO'))

DAILY = "Daily"
HOURLY = "Hourly"
WEEKLY = "Weekly"

ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "
EXCEPTION_BODY_MESSAGE = "Manhattan failed due to the following:\n\n{}\n\nPlease check the logs!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"
FAILURE_MESSAGE = "One or more feeds are down or submitting abnormal amounts of domains!"
PAGER_MESSAGE = 'One or more feeds have been running longer than a day! Please check your email for details!'
STUCK_TASKS_MESSAGE = 'One or more feeds have been running longer than a day:\n{}\nThese feeds must be manually ' \
                      'stopped within AWS console here: {}\n'
SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
SUBJECT_MESSAGE = "Manhattan detected an issue"
SUCCESS_MESSAGE = "feeds are up and running normally!"

ERROR_FEEDS = "Downed feeds: "
LOG_GROUP_NAME = 'feed-eaters-prod'
TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"

CLUSTER_NAME = settings('ecs.feeds.cluster')
FEED_URL = settings('ecs.feeds.url')
PAGER_SNS = settings('sns.pager')
SNS_TOPIC_ARN = settings('manhattan.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

FEEDS_TO_CHECK_HOURLY = {
    'bambenek_c2_ip': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 1, 'max': 20000},
    'cox_feed': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 1, 'max': 1000000},
    'Xylitol_CyberCrime': {'metric_name': 'URI', 'min': 1, 'max': 500},
    'ecrimeX': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 10, 'max': 2000},
    'G01Pack_DGA': {'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 1, 'max': 1000},
    'tracker_h3x_eu': {'metric_name': 'URI', 'min': 1, 'max': 2000},
    'VX_Vault': {'metric_name': 'URI', 'min': 1, 'max': 100},
    'Ransomware_tracker': {'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 1, 'max': 1000},
    'Zeus_Tracker': {'metric_name': 'URI_TIDE_SUCCESS', 'min': 1, 'max': 1000}
}

FEEDS_HOURLY_NAMES = [
                      'bambenek-ip-scraper', 'cox-feed', 'cybercrime-scraper', 'ecrimex-scraper',
                      'g01-dga', 'tracker-h3x-eu-scraper', 'vxvault-scraper', 'ransomware-tracker-scraper',
                      'zeus-tracker-scraper'
]

FEEDS_TO_CHECK_DAILY = {
    'bambenek_OSINT_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 40000, 'max': 300000, 'hour_submitted': '11'
    },
    'CryptoLocker_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 1, 'max': 10000, 'hour_submitted': '09'
    },
    'feodo_tracker': {
        'metric_name': 'IPV4_TIDE_SUCCESS', 'min': 50, 'max': 200, 'hour_submitted': '21'
    },
    'FastFlux_GameoverZeus_DGA': {
        'metric_name': 'FQDN_TIDE_SUCCESS', 'min': 1, 'max': 40000, 'hour_submitted': '10'
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
                     'bambenek-dga', 'feodo-scraper', 'ff-goz-dga', 'locky-dga-scraper', 'malc0de-scraper',
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


def find_bad_feeds(event_type, watcher):
    """
    Find all the feeds that are down and/or out of range
    @param event_type: Whether the check is Weekly, Daily, or Hourly
    @param watcher: watchmen object
    @return: tuple of lists: list of all the down feeds and list of out of range feeds or None upon exception
    """
    downed_feeds = []
    submitted_out_of_range_feeds = []

    try:
        end = datetime.now(tz=pytz.utc)
        if event_type == HOURLY:
            start = end - timedelta(hours=1)
            downed_feeds = watcher.process_feeds_logs(FEEDS_HOURLY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_HOURLY, TABLE_NAME, 0
            )
        elif event_type == DAILY:
            start = end - timedelta(days=1)
            downed_feeds = watcher.process_feeds_logs(FEEDS_DAILY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_DAILY, TABLE_NAME, 1
            )
        elif event_type == WEEKLY:
            start = end - timedelta(days=7)
            downed_feeds = watcher.process_feeds_logs(FEEDS_WEEKLY_NAMES, start, end)
            submitted_out_of_range_feeds = watcher.process_feeds_metrics(
                FEEDS_TO_CHECK_WEEKLY, TABLE_NAME, 2
            )
        return downed_feeds, submitted_out_of_range_feeds
    except Exception as ex:
        LOGGER.error(ex)
        trace = traceback.format_exc(ex)
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_BODY_MESSAGE.format(trace), SUBJECT_EXCEPTION_MESSAGE)
        return None


def find_stuck_tasks(watcher):
    """
    Find the task that are stuck in the given cluster
    @param watcher: watchmen object
    @return: list of all the stuck tasks or None upon exception
    """
    try:
        stuck_tasks = watcher.get_stuck_ecs_tasks(CLUSTER_NAME)
        return stuck_tasks
    except Exception as ex:
        LOGGER.error(ex)
        trace = traceback.format_exc(ex)
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_BODY_MESSAGE.format(trace), SUBJECT_EXCEPTION_MESSAGE)
        return None


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    watcher = Watchmen(log_group_name=LOG_GROUP_NAME)
    event_type = event.get('type')

    stuck_tasks = find_stuck_tasks(watcher)
    bad_feeds = find_bad_feeds(event_type, watcher)
    summarized_result = summarize(event_type, stuck_tasks, bad_feeds)

    LOGGER.info(summarized_result)
    status = notify(summarized_result)

    return status


def notify(summarized_result):
    """
    Using the results passed in, this function will send an email (and sometimes pager alarm) upon failures or exception
    @param summarized_result: dict containing all information to send alert
    @return: the status of the check
    """
    status = SUCCESS_MESSAGE

    if summarized_result is None:
        return "Failure: an exception occurred during checking process.\n{}".format(EXCEPTION_MESSAGE)

    message = summarized_result.get("message")
    subject = summarized_result.get("subject")
    success = summarized_result.get("success")

    if not success:
        status = FAILURE_MESSAGE
        raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
        if summarized_result.get("pager_message"):
            raise_alarm(PAGER_SNS, PAGER_MESSAGE, subject)

    return status


def summarize(event_type, stuck_tasks, bad_feeds):
    """
    Summarizes the results from feed checks and creates a dict ready for email notifications
    @param event_type: whether the check is Hourly, Daily, or Weekly
    @param stuck_tasks: list of all the stuck tasks or None upon exception
    @param bad_feeds: tuple of lists of the down feeds and the out of range feeds
    @return: a dict to be readily used for the notification process
    """
    if stuck_tasks is None and bad_feeds is None:
        return None

    down = bad_feeds[0]
    out_of_range = bad_feeds[1]

    all_stuck = ""
    all_down = ""
    all_range = ""
    for stuck in stuck_tasks:
        all_stuck += "{}\n".format(stuck)
    for down_feeds in down:
        all_down += "{}\n".format(down_feeds)
    for oor in out_of_range:
        all_range += "{}\n".format(oor)

    subject_line = SUBJECT_MESSAGE
    message_body = ""
    pager_message = ""
    success = True
    # Check for stuck tasks
    if stuck_tasks:
        subject_line += ' | Feeds ECS Cluster Has Hung Tasks'
        message_body += STUCK_TASKS_MESSAGE.format(all_stuck, FEED_URL)
        pager_message = PAGER_MESSAGE
        success = False

    # Check if any feeds are down or out of range
    if down or out_of_range:
        subject_line += ' | One or more feeds are down!'
        message_body += "\n\n\n{}\n".format('-' * 60) if message_body else ""
        message_body += '{}: {}\n{}\n{}\n{}\n{}\n'.format(
            event_type,
            FAILURE_MESSAGE,
            ERROR_FEEDS,
            all_down,
            ABNORMAL_SUBMISSIONS_MESSAGE,
            all_range)
        success = False

    # LOGGER.debug(subject_line)
    # LOGGER.debug(message_body)

    return {
        "subject": subject_line,
        "message": message_body,
        "success": success,
        "pager_message": pager_message
    }
