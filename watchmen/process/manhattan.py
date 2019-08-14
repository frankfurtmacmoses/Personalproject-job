"""
Created on July 30, 2018
This script is designed to monitor daily, hourly, and weekly feeds and ensure proper data flow.
@author: Daryan Hanshew
@email: dhanshew@infoblox.com
"""
# Python imports
import json
import os
import traceback
from datetime import datetime, timedelta
import pytz
# Watchmen imports
from watchmen.utils.ecs import get_stuck_ecs_tasks
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.logger import get_logger
from watchmen.utils.feeds import process_feeds_metrics, process_feeds_logs
from watchmen.config import settings

LOGGER = get_logger("Manhattan", settings('logging.level', 'INFO'))

DAILY = "Daily"
HOURLY = "Hourly"
WEEKLY = "Weekly"

ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "
EXCEPTION_BODY_MESSAGE = "Manhattan failed due to the following:\n\n{}\n\nPlease check the logs!"
EXCEPTION_MESSAGE = "Please check logs for more details about exception!"
FAILURE_MESSAGE = "One or more feeds are down or submitting abnormal amounts of domains!"
FILE_FAILURE_MESSAGE = "Cannot load feeds to check from file:\n{}\nException:{}"
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

JSON_NAME = "feeds_to_check.json"
FILE_PATH = os.path.dirname(os.path.realpath(__file__))


def find_bad_feeds(event_type):
    """
    Find all the feeds that are down and/or out of range
    IMPORTANT NOTE: Feeds to check weekly has to run on Friday in order to ensure proper date traversal!
    How it works:
                   Monday: 4
                   Tuesday: 3
                   Wednesday: 2
                   Thursday: 1
                   Friday: 0
                   To check for monday you subtract 4 days from the run day on Friday.
                   IE If the date is 08/10/2018 and I want to check feeds running on Monday
                then I subtract 4 days to 08/06/2018 and check the dynamodb metrics table.
    @param event_type: Whether the check is Weekly, Daily, or Hourly
    @return: tuple of lists: list of all the down feeds and list of out of range feeds or None upon exception
    """

    downed_feeds = []
    submitted_out_of_range_feeds = []
    feeds_dict = load_feeds_to_check()
    # Make sure data loaded correctly
    if not feeds_dict:
        return None

    feeds_to_check_hourly = feeds_dict.get(HOURLY)
    feeds_to_check_daily = feeds_dict.get(DAILY)
    feeds_to_check_weekly = feeds_dict.get(WEEKLY)

    feeds_hourly_names = [item.get("name") for item in feeds_to_check_hourly]
    feeds_daily_names = [item.get("name") for item in feeds_to_check_daily]

    feeds_weekly_names = [item.get("name") for item in feeds_to_check_weekly]

    try:
        end = datetime.now(tz=pytz.utc)
        event_type_content = {
            HOURLY: {
                "feeds_names": feeds_hourly_names,
                "start": end - timedelta(hours=1),
                "end": end,
                "feeds_to_check": feeds_to_check_hourly,
                "table_name": TABLE_NAME,
                "time_string_choice": 0,
            },
            DAILY: {
                "feeds_names": feeds_daily_names,
                "start": end - timedelta(days=1),
                "end": end,
                "feeds_to_check": feeds_to_check_daily,
                "table_name": TABLE_NAME,
                "time_string_choice": 1,
            },
            WEEKLY: {
                "feeds_names": feeds_weekly_names,
                "start": end - timedelta(days=7),
                "end": end,
                "feeds_to_check": feeds_to_check_weekly,
                "table_name": TABLE_NAME,
                "time_string_choice": 2,
            }
        }
        if event_type in event_type_content:
            downed_feeds = process_feeds_logs(
                event_type_content.get(event_type).get("feeds_names"),
                event_type_content.get(event_type).get("start"),
                event_type_content.get(event_type).get("end"),
                LOG_GROUP_NAME
            )
            submitted_out_of_range_feeds = process_feeds_metrics(
                event_type_content.get(event_type).get("feeds_to_check"),
                event_type_content.get(event_type).get("table_name"),
                event_type_content.get(event_type).get("time_string_choice")
            )
        return downed_feeds, submitted_out_of_range_feeds
    except Exception as ex:
        LOGGER.exception(traceback.extract_stack())
        LOGGER.info('*' * 80)
        LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
        return None


def find_stuck_tasks():
    """
    Find the task that are stuck in the given cluster
    @return: list of all the stuck tasks or None upon exception
    """
    try:
        stuck_tasks = get_stuck_ecs_tasks(CLUSTER_NAME)
        return stuck_tasks
    except Exception as ex:
        LOGGER.exception(traceback.extract_stack())
        LOGGER.info('*' * 80)
        LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
        return None


def load_feeds_to_check():
    """
    Load feeds to check from config file
    @return: <dict> a dictionary including feeds to check
    """
    json_path = os.path.join(FILE_PATH, JSON_NAME)

    try:
        with open(json_path) as file:
            feeds_dict = json.load(file)
        return feeds_dict
    except Exception as ex:
        msg = FILE_FAILURE_MESSAGE.format(json_path, ex)
        LOGGER.error(msg)
        return None


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    event_type = event.get('type')

    stuck_tasks = find_stuck_tasks()
    bad_feeds = find_bad_feeds(event_type)
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
        "pager_message": pager_message,
    }
