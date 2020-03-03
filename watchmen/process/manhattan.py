"""
Created on July 30, 2018
This script is designed to monitor Reaper's daily, hourly, and weekly feeds and ensure proper data flow.
@author: Daryan Hanshew
@email: dhanshew@infoblox.com

Refactored with Watchman interface on October 3, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
# Python imports
from datetime import datetime, timedelta
import json
import os
import pytz
import traceback

# Watchmen imports
from watchmen import const
from watchmen import messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings
from watchmen.utils.ecs import get_stuck_ecs_tasks
from watchmen.utils.feeds import process_feeds_metrics, process_feeds_logs

# Event Types
HOURLY = "Hourly"
DAILY = "Daily"
WEEKLY = "Weekly"

ALL_EVENT_TYPES = [HOURLY, DAILY, WEEKLY]

# Messages
MESSAGES = messages.MANHATTAN

# DynamoDB and Files
CLUSTER_NAME = settings('ecs.feeds.cluster', 'cyberint-feed-eaters-prod-EcsCluster-L94N32MQ0KU8')
FEED_URL = settings(
    'ecs.feeds.url',
    'https://console.aws.amazon.com/ecs/home?region=us-east-1#/'
    'clusters/cyberint-feed-eaters-prod-EcsCluster-L94N32MQ0KU8/services')
FILE_PATH = os.path.dirname(os.path.realpath(__file__))
JSON_FILE = settings('manhattan.json_file')
LOG_GROUP_NAME = settings('manhattan.log_group_name', 'feed-eaters-prod')
TABLE_NAME = settings(
    'manhattan.table_name',
    'CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ')

# Manhattan profile
TARGET = "Reaper Feeds"
PAGER_TARGET = "Pager Duty"


class Manhattan(Watchman):
    """
    class of Manhattan
    """
    def __init__(self, event, context):
        """
        constructor of Manhattan
        @param event: <dict> dict containing string of event type including: Daily, Hourly, and Weekly
        """
        super().__init__()
        self.event = event.get("Type")

    def monitor(self) -> [Result]:
        """
        Monitors the Reaper feeds hourly, daily, or weekly.
        @return: <Result> List of Result objects
        """
        if self._check_invalid_event():
            return self._create_invalid_event_results()
        stuck_tasks, find_st_tb = self._find_stuck_tasks()
        bad_feeds, find_bf_tb = self._find_bad_feeds()
        snapshot = self._create_snapshot(stuck_tasks, bad_feeds)
        tb = self._create_tb_details(find_bf_tb, find_st_tb)
        summary = self._create_summary(stuck_tasks, bad_feeds, tb)
        results = self._create_results(summary, snapshot)
        return results

    def _build_bad_tasks_message(self, task_list):
        message = ""
        for task in task_list:
            message += "\n\t- {}".format(task)
        return message

    def _check_invalid_event(self):
        """
        Method to check that the event passed in from the Lambda has the correct parameters. If there is no "Type"
        parameter passed in, or the "Type" does not equal any of the expected values ("Hourly", "Daily", or "Weekly"),
        then the event parameter is invalid.
        :return: True if the event parameter passed from the Lambda is invalid, false if the event parameter is valid.
        """
        if not self.event or self.event not in ALL_EVENT_TYPES:
            self.logger.info(MESSAGES.get("failed_event_check").format(self.event))
            return True

        self.logger.info(MESSAGES.get("success_event_check"))
        return False

    def _create_invalid_event_results(self):
        """
        Method to create the results for the scenario when the Lambda sends in invalid event parameters.
        :return: Two result objects, one for the pager SNS topic and one for the email SNS topic.
        """
        exception_results = []

        exception_results.append(Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_invalid_event_subject"),
            source=self.source,
            target=TARGET,
            details=MESSAGES.get("exception_invalid_event_message"),
            snapshot={},
            message=MESSAGES.get("exception_message"),
        ))

        # result for Pager Duty SNS
        exception_results.append(Result(
            disable_notifier=False,
            state=Watchman.STATE.get("exception"),
            success=False,
            subject=MESSAGES.get("exception_invalid_event_subject"),
            source=self.source,
            target=PAGER_TARGET,
            # Pager Duty requires a short message
            details=MESSAGES.get("exception_message"),
            snapshot={},
            message=MESSAGES.get("exception_message"),
        ))

        return exception_results

    def _create_results(self, summary, snapshot):
        """
        Create [Result] list.
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
        results = []

        # Result for email SNS
        check_result = summary.get("success")
        subject = summary.get("subject")
        details = summary.get("details")
        message = summary.get("message")
        parameters = parameter_chart.get(check_result)
        results.append(Result(
            **parameters,
            success=check_result,
            subject=subject,
            source=self.source,
            target=TARGET,
            details=details,
            snapshot=snapshot,
            message=message,
        ))

        # result for Pager Duty SNS
        results.append(Result(
            **parameters,
            success=check_result,
            subject=subject,
            source=self.source,
            target=PAGER_TARGET,
            # Pager Duty requires a short message
            details=message,
            snapshot=snapshot,
            message=message,
        ))

        return results

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
            no_metrics = bad_feeds[2]
            if down:
                result["down_feeds"] = down
            if out_of_range:
                result["out_of_range_feeds"] = out_of_range
            if no_metrics:
                result["no_metrics_feeds"] = no_metrics
        return result

    def _create_summary(self, stuck_tasks, bad_feeds, tb):
        """
        Summarizes the results from feed checks and creates a dict ready for email notifications
        @param stuck_tasks: <list> list of all the stuck tasks or None upon exception
        @param bad_feeds: <tuple> tuple of lists of the down feeds and the out of range feeds
        @param tb: <str> traceback, return summary of exception otherwise None
        @return: <dict> a dict to be readily used for the notification process
        """
        event = self.event

        # return exception set if tb
        if tb:
            return {
                "subject": MESSAGES.get("subject_exception_message"),
                "details": tb,
                "success": None,
                "message": MESSAGES.get("exception_message"),
            }

        down = bad_feeds[0]
        out_of_range = bad_feeds[1]
        no_metrics = bad_feeds[2]

        all_stuck = self._build_bad_tasks_message(stuck_tasks)
        all_down = self._build_bad_tasks_message(down)
        all_range = self._build_bad_tasks_message(out_of_range)
        all_no = self._build_bad_tasks_message(no_metrics)

        # If success, return success information
        subject_line = MESSAGES.get("success_subject").format(event)
        details_body = ""
        success = True
        message = MESSAGES.get("success_message")

        # Check for stuck tasks
        if stuck_tasks:
            subject_line = "{} {}{}".format(
                event,
                MESSAGES.get("failure_subject"),
                " | Stuck Tasks"
            )
            details_body = "{}\n\n{}\n\n".format(
                MESSAGES.get("stuck_tasks_message").format(all_stuck, FEED_URL),
                const.LINE_SEPARATOR
            )
            message = "FAILURE: Stuck Tasks" + const.LINE_SEPARATOR
            success = False

        # Check if any feeds are down.
        if down:
            if success:
                subject_line = "{} {}".format(
                    event,
                    MESSAGES.get("failure_subject"),
                )
                message = "FAILURE: "
            subject_line += ' | Down'
            details_body += '{}{}\n\n{}\n\n'.format(
                MESSAGES.get("failure_down_message"),
                all_down,
                const.LINE_SEPARATOR
            )
            message += "Down feeds" + const.LINE_SEPARATOR
            success = False

        # Check if any feeds are out of threshold range.
        if out_of_range:
            if success:
                subject_line = "{} {}".format(
                    event,
                    MESSAGES.get("failure_subject"),
                )
                message = "FAILURE: "
            subject_line += " | Out of Range"
            details_body += '{}{}\n\n{}\n\n'.format(
                MESSAGES.get("failure_abnormal_message"),
                all_range,
                const.LINE_SEPARATOR
            )
            message += "Out of range feeds" + const.LINE_SEPARATOR
            success = False

        # Check if any feeds have no metrics
        if no_metrics:
            if success:
                subject_line = "{} {}".format(
                    event,
                    MESSAGES.get("failure_subject"),
                )
                message = "FAILURE: "
            subject_line += ' | No Metrics'
            details_body += "{}".format(MESSAGES.get("no_metrics_message").format(all_no))
            message += "Feeds with no metrics" + const.LINE_SEPARATOR
            success = False

        # If check was not a success, need to add extra line to message for Pager Duty
        if not success:
            message += MESSAGES.get("check_email_message")

        return {
            "subject": subject_line,
            "details": details_body,
            "success": success,
            "message": message,
        }

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
            result = MESSAGES.get("exception_details_start")
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
        no_metrics_feeds = []
        event = self.event

        feeds_dict, tb = self._load_feeds_to_check()
        # Make sure data loaded correctly
        if not feeds_dict:
            return (None, None, None), tb

        feeds_to_check_hourly = feeds_dict.get(HOURLY)
        feeds_to_check_daily = feeds_dict.get(DAILY)
        feeds_to_check_weekly = feeds_dict.get(WEEKLY)

        # Only adding names for each feed if it has a 'name' key; Doesn't add None to list
        feeds_hourly_names = [item.get("name") for item in feeds_to_check_hourly if item.get("name")]
        feeds_daily_names = [item.get("name") for item in feeds_to_check_daily if item.get("name")]
        feeds_weekly_names = [item.get("name") for item in feeds_to_check_weekly if item.get("name")]

        try:
            end = datetime.now(tz=pytz.utc)
            event_content = {
                HOURLY: {
                    "feeds_names": feeds_hourly_names,
                    "start": end - timedelta(hours=1),
                    "end": end,
                    "feeds_to_check": feeds_to_check_hourly,
                    "table_name": TABLE_NAME
                },
                DAILY: {
                    "feeds_names": feeds_daily_names,
                    "start": end - timedelta(days=1),
                    "end": end,
                    "feeds_to_check": feeds_to_check_daily,
                    "table_name": TABLE_NAME
                },
                WEEKLY: {
                    "feeds_names": feeds_weekly_names,
                    "start": end - timedelta(days=7),
                    "end": end,
                    "feeds_to_check": feeds_to_check_weekly,
                    "table_name": TABLE_NAME
                }
            }
            if event in event_content:
                downed_feeds = process_feeds_logs(
                    event_content.get(event).get("feeds_names"),
                    event_content.get(event).get("start"),
                    event_content.get(event).get("end"),
                    LOG_GROUP_NAME
                )
                submitted_out_of_range_feeds, no_metrics_feeds = process_feeds_metrics(
                    event_content.get(event).get("feeds_to_check"),
                    event_content.get(event).get("table_name"),
                    event
                )
            return (downed_feeds, submitted_out_of_range_feeds, no_metrics_feeds), None
        except Exception as ex:
            self.logger.exception(traceback.extract_stack())
            self.logger.info(const.MESSAGE_SEPARATOR)
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
            self.logger.info(const.MESSAGE_SEPARATOR)
            self.logger.exception('{}: {}'.format(type(ex).__name__, ex))
            tb = traceback.format_exc()
            return None, tb

    def _load_feeds_to_check(self):
        """
        Load feeds to check from config file
        @return: <dict> a dictionary including feeds to check
        @return: <str> error message
        """
        json_path = os.path.join(FILE_PATH, JSON_FILE)
        try:
            with open(json_path) as file:
                feeds_dict = json.load(file)
            return feeds_dict, None
        except Exception as ex:
            fmt = "Cannot load feeds to check from file:\n{}\nException: {}"
            msg = fmt.format(json_path, type(ex).__name__)
            self.logger.error(msg)
            return None, msg
