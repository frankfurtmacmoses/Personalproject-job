"""
Created on July 30, 2018
This script is designed to monitor Reaper's daily, hourly, and weekly feeds and ensure proper data flow.
@author: Daryan Hanshew
@email: dhanshew@infoblox.com

Refactored with Watchman interface on July 18, 2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""
# Python imports
from datetime import datetime, timedelta
import json
import os
import pytz
import traceback
# Watchmen imports
from watchmen import const
from watchmen.utils.ecs import get_stuck_ecs_tasks
from watchmen.utils.feeds import process_feeds_metrics, process_feeds_logs
from watchmen.common.result import DEFAULT_MESSAGE, Result
from watchmen.config import settings
from watchmen.common.watchman import Watchman

DAILY = "Daily"
HOURLY = "Hourly"
WEEKLY = "Weekly"

ABNORMAL_SUBMISSIONS_MESSAGE = "Abnormal submission amount from these feeds: "
EXCEPTION_DETAILS_START = "Manhattan failed due to the following:"
EXCEPTION_DETAILS_END = "Please check the logs!"
FAILURE_MESSAGE = "One or more feeds are down or submitting abnormal amounts of domains!"
STUCK_TASKS_MESSAGE = 'One or more feeds have been running longer than a day:\n{}\nThese feeds must be manually ' \
                      'stopped within AWS console here: {}\n'
SUBJECT_EXCEPTION_MESSAGE = "Manhattan watchmen failed due to an exception!"
FAILURE_SUBJECT = "Manhattan detected an issue"
SUCCESS_SUBJECT = "{} feeds works for Manhattan watchmen are up and running!"
SUCCESS_MESSAGE = "Feeds are up and running normally!"
ERROR_FEEDS = "\nDowned feeds: "
LOG_GROUP_NAME = settings('manhattan.log_group_name', 'feed-eaters-prod')
PAGER_MESSAGE = 'One or more feeds have been running longer than a day! See details in email!'
TABLE_NAME = settings(
    'manhattan.table_name',
    'CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ')

CLUSTER_NAME = settings('ecs.feeds.cluster', 'cyberint-feed-eaters-prod-EcsCluster-L94N32MQ0KU8')
FEED_URL = settings(
    'ecs.feeds.url',
    'https://console.aws.amazon.com/ecs/home?region=us-east-1#/'
    'clusters/cyberint-feed-eaters-prod-EcsCluster-L94N32MQ0KU8/services')

JSON_NAME = "feeds_to_check.json"
FILE_PATH = os.path.dirname(os.path.realpath(__file__))

# watchmen profile
TARGET = "Reaper Feeds"


class Manhattan(Watchman):
    """
    class of Manhattan
    """
    def __init__(self, event_type):
        """
        constructor of Manhattan
        @param event_type: <dict> dict containing string of event type including: Daily, Hourly, and Weekly
        """
        super().__init__()
        self.event_type = event_type.get("type")

    def monitor(self) -> Result:
        """
        Monitors the Reaper feeds hourly, daily, or weekly.
        @return: <Result> Result object
        """
        stuck_tasks, find_st_tb = self._find_stuck_tasks()
        bad_feeds, find_bf_tb = self._find_bad_feeds()
        snapshot = self._create_snapshot(stuck_tasks, bad_feeds)
        tb = self._create_tb_details(find_bf_tb, find_st_tb)
        summary = self._create_summary(stuck_tasks, bad_feeds, tb)
        result = self._create_result(summary, snapshot)
        return [result]

    def _create_result(self, summary, snapshot):
        """
        Create Result object.
        @param: <dict> summary that includes subject, details, success, stuck_tasks
        @param: <dict> snapshot including stuck_task, bad feeds
        @return: <Result> Result object
        """
        parameter_chart = {
            True: {
                "disable_notifier": True,
                "state": Watchman.STATE.get("success"),
            },
            False: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("failure"),
            },
            None: {
                "disable_notifier": False,
                "state": Watchman.STATE.get("exception"),
            }
        }
        check_result = summary.get("success")
        subject = summary.get("subject")
        details = summary.get("details")
        message = summary.get("message")
        parameters = parameter_chart.get(check_result)
        result = Result(
            **parameters,
            success=check_result,
            subject=subject,
            source=self.source,
            target=TARGET,
            details=details,
            snapshot=snapshot,
            message=message,
        )
        return result

    def _create_summary(self, stuck_tasks, bad_feeds, tb):
        """
        Summarizes the results from feed checks and creates a dict ready for email notifications
        @param stuck_tasks: <list> list of all the stuck tasks or None upon exception
        @param bad_feeds: <tuple> tuple of lists of the down feeds and the out of range feeds
        @param tb: <str> traceback, return summary of exception if not None
        @return: <dict> a dict to be readily used for the notification process
        """
        event_type = self.event_type
        # return exception set if tb
        if tb:
            return {
                "subject": SUBJECT_EXCEPTION_MESSAGE,
                "details": tb,
                "success": None,
                "message": DEFAULT_MESSAGE,
            }
        down = bad_feeds[0]
        out_of_range = bad_feeds[1]

        all_stuck = ""
        all_down = ""
        all_range = ""
        for stuck in stuck_tasks:
            all_stuck += "{}\n".format(stuck)
        for down_feeds in down:
            all_down += "- {}\n".format(down_feeds)
        for oor in out_of_range:
            all_range += "- {}\n".format(oor)

        # set subject line to success first
        subject_line = SUCCESS_SUBJECT.format(event_type)
        details_body = ""
        success = True
        message = DEFAULT_MESSAGE
        # Check for stuck tasks
        if stuck_tasks:
            # once there is one problem happening, change the subject line to failure
            subject_line = FAILURE_SUBJECT + ' | Feeds ECS Cluster Has Hung Tasks'
            details_body += STUCK_TASKS_MESSAGE.format(all_stuck, FEED_URL)
            message = PAGER_MESSAGE
            success = False

        # Check if any feeds are down or out of range
        if down or out_of_range:
            if success:
                subject_line = FAILURE_SUBJECT
            subject_line += ' | One or more feeds are down!'
            details_body += "\n{}\n".format('-' * 60) if details_body else ""
            details_body += '{}: {}\n{}\n{}\n{}\n{}\n'.format(
                self.event_type,
                FAILURE_MESSAGE,
                ERROR_FEEDS,
                all_down,
                ABNORMAL_SUBMISSIONS_MESSAGE,
                all_range)
            success = False

        return {
            "subject": subject_line,
            "details": details_body,
            "success": success,
            "message": message,
        }

    @staticmethod
    def _create_snapshot(stuck_tasks, bad_feeds):
        """
        Create a snapshot based on stuck tasks and bad feeds.
        @return: <dict> snapshot
        """
        result = {}
        if stuck_tasks:
            stuck_list = []
            for stuck in stuck_tasks:
                stuck_list.append(stuck.get("taskDefinitionArn"))
            result["stuck_tasks"] = stuck_list

        if bad_feeds:
            down = bad_feeds[0]
            out_of_range = bad_feeds[1]
            if down:
                result["down_feeds"] = down
            if out_of_range:
                result["out_of_range_feeds"] = out_of_range
        return result

    @staticmethod
    def _create_tb_details(find_bf_tb, find_st_tb):
        """
        Combines two tracebacks and make a detailed message.
        @param find_bf_tb: <str> traceback while finding bad feeds
        @param find_st_tb: <str> traceback while finding stuck tasks
        @return: <str> detailed traceback message
        """
        result = None
        if find_bf_tb or find_st_tb:
            result = EXCEPTION_DETAILS_START
        if find_bf_tb:
            result += "\n\n* when finding bad feed: {}".format(find_bf_tb)
        if find_st_tb:
            result += "\n\n* when finding stuck tasks: {}".format(find_st_tb)
        return result

    def _find_bad_feeds(self):
        """
        Find all the feeds that are down and/or out of range
        IMPORTANT NOTE: This has to run on Friday in order to ensure proper date traversal!
        How it works:
                      Monday: 4
                      Tuesday: 3
                      Wednesday: 2
                      Thursday: 1
                      Friday: 0
                      To check for monday you subtract 4 days from the run day on Friday.
                      IE If the date is 08/10/2018 and I want to check feeds running on Monday
                    then I subtract 4 days to 08/06/2018 and check the dynamodb metrics table.

        @return: <list, list> <str>
        <list, list>: list of all the down feeds, list of out of range feeds, either list can be None upon exception
        <str>: traceback
        """
        downed_feeds = []
        submitted_out_of_range_feeds = []
        event_type = self.event_type

        feeds_dict, tb = self._load_feeds_to_check()
        # Make sure data loaded correctly
        if not feeds_dict:
            return (None, None), tb

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
            return (downed_feeds, submitted_out_of_range_feeds), None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info('*' * const.LENGTH_OF_PRINT_LINE)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return (None, None), tb

    def _find_stuck_tasks(self):
        """
        Find the tasks that are stuck in the given cluster.
        @return: <list> <str>
        <list> list of all the stuck tasks or None upon exception
        <str> traceback or None upon success
        """
        try:
            stuck_tasks = get_stuck_ecs_tasks(CLUSTER_NAME)
            return stuck_tasks, None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info('*' * const.LENGTH_OF_PRINT_LINE)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _load_feeds_to_check(self):
        """
        Load feeds to check from config file
        @return: <dict> a dictionary including feeds to check
        @return: <str> error message
        """
        json_path = os.path.join(FILE_PATH, JSON_NAME)
        try:
            with open(json_path) as file:
                feeds_dict = json.load(file)
            return feeds_dict, None
        except Exception as ex:
            fmt = "Cannot load feeds to check from file:\n{}\nException: {}"
            msg = fmt.format(json_path, type(ex).__name__)
            self.logger.error(msg)
            return None, msg


# the following blocked out code is for local testing in the future


# from mock import patch
#
#
# @patch('watchmen.models.manhattan.Manhattan._find_stuck_tasks')
# @patch('watchmen.models.manhattan.Manhattan._find_bad_feeds')
# def run(mock_bf, mock_st):
#     manhattan_obj = Manhattan({"type": "Hourly"})
#     down_feeds = ["down1", "down2", "down3", "down4"]
#     oor_feeds = [
#         "feodo_tracker 1:\n  Amount Submitted: 30, Min Submission Amount: 50, Max Submission Amount: 200",
#         "feodo_tracker 2:\n  Amount Submitted: 30, Min Submission Amount: 50, Max Submission Amount: 200",
#         "feodo_tracker 3:\n  Amount Submitted: 30, Min Submission Amount: 50, Max Submission Amount: 200",
#         "feodo_tracker 4:\n  Amount Submitted: 30, Min Submission Amount: 50, Max Submission Amount: 200"
#     ]
#     mock_bf.return_value = (down_feeds, oor_feeds), None
#     mock_st.return_value = [{"taskDefinitionArn": "example arn topic yeah"}], None
#     manhattan_obj._find_bad_feeds = mock_bf
#     manhattan_obj._find_stuck_tasks = mock_st
#     results = manhattan_obj.monitor()
#     print("Result: ", results[0])
#     from watchmen.common.result_svc import ResultSvc
#     result_svc = ResultSvc(results)
#     result_svc.send_alert()
#
#
# if __name__ == "__main__":
#     run()
