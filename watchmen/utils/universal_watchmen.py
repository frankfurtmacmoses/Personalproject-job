"""
Created on July 17, 2018

This module is meant to be used as a helper for other
Watchmen scripts. Most of this class can be utilized
for verifying simple checks in S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

"""
# Python imports
from datetime import datetime, timedelta
from logging import getLogger, basicConfig, INFO
import pytz
# External Libraries
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

LOGGER = getLogger("Universal Watchmen")
basicConfig(level=INFO)

FILE_NOT_FOUND_ERROR_MESSAGE = "FILE DOESN'T EXIST!"
FILE_SIZE_ZERO_ERROR_MESSAGE = "FILE SIZE IS ZERO!"
EMPTY_METRIC_ERROR = "No metric found for: "


class Watchmen(object):
    """
    universal watchmen class
    """
    def __init__(self, bucket_name='', log_group_name=''):
        basicConfig(level=INFO)
        self.s3_client = boto3.resource('s3')
        self.dynamo_client = boto3.resource('dynamodb')
        self.log_client = boto3.client('logs')
        self.bucket_name = bucket_name
        self.log_group_name = log_group_name

    def validate_file_on_s3(self, key):
        """
        Checks if a file exists on S3 and non-zero size.
        :param key: path to the file
        :return: true if file exists otherwise false
        """
        file_obj = self.s3_client.Object(self.bucket_name, key)
        is_valid_file = True
        try:
            # Checks file size if it's zero
            if file_obj.get()['ContentLength'] == 0:
                is_valid_file = False
                LOGGER.info(FILE_SIZE_ZERO_ERROR_MESSAGE)
        except ClientError:
            # Means the file doesn't exist
            is_valid_file = False
            LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)

        return is_valid_file

    def get_file_contents_s3(self, key):
        """
        Retrieves file contents for a file on S3 and streams it over.
        :param key: path to the file
        :return: the contents of the file if they exist otherwise none
        """
        try:
            file_contents = self.s3_client.Object(self.bucket_name, key).get()['Body'].read()
        except ClientError:
            file_contents = None
            LOGGER.info(FILE_NOT_FOUND_ERROR_MESSAGE)
        return file_contents

    def select_dynamo_time_string(self, feeds_to_check, feed, time_string_choice):
        """
        Selects the time string to use based off choice.
        :param feeds_to_check: feeds currently being looked at
        :param feed: the feed itself being checked
        :param time_string_choice: the selection for time string by user
                0 = hourly, 1 = daily, 2 = weekly
        :return: time string for dynamo db
        """
        time_string = None
        if time_string_choice == 0:
            time_string = self.get_dynamo_hourly_time_string()
        elif time_string_choice == 1:
            time_string = self.get_dynamo_daily_time_string(feeds_to_check.get(feed).get('hour_submitted'))
        elif time_string_choice == 2:
            time_string = self.get_dynamo_weekly_time_string(
                                                             feeds_to_check.get(feed).get('hour_submitted'),
                                                             feeds_to_check.get(feed).get('days_to_subtract')
            )
        return time_string

    def get_feed_metrics(self, table_name, feed, check_time):
        """
        Retrieves metrics for a particular feed.
        :param table_name: name of table being searched
        :param feed: feed itself being checked
        :param check_time: time being checked in metrics table
        :return: metrics for a particular feed
        """
        metric = {}
        table = self.dynamo_client.Table(table_name)
        response = table.query(
            KeyConditionExpression=Key('timestamp').eq(check_time)
        )
        for item in response.get('Items'):
            if item.get('source') == feed:
                metric = item.get('metric')
                break

        if not metric:
            LOGGER.info(EMPTY_METRIC_ERROR + feed)
        return metric

    def process_feeds_logs(self, feed_names, start, end):
        """
        Processes all the logs for feeds and ensures that a log was created.
        :param feed_names: names of all feeds submitting to Reaper
        :param start: start time of processing logs
        :param end: end time of processing logs
        :return: a list if any feeds that are suspected to be down
        """
        response = None
        feed_name_set = set()
        downed_feeds = []
        while start < end:
            if not response:
                response = self.log_client.describe_log_streams(
                    logGroupName=self.log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=50
                )
            else:
                response = self.log_client.describe_log_streams(
                    logGroupName=self.log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    nextToken=response.get('nextToken'),
                    limit=50
                )
            for log_stream in response.get('logStreams'):
                log_time = datetime.fromtimestamp(log_stream.get('lastEventTimestamp') / 1000, pytz.utc)
                feed_name = log_stream.get('logStreamName').split('/')[0]
                if start < log_time < end:
                    feed_name_set.add(feed_name)
                end = log_time
        for feed in feed_names:
            if feed not in feed_name_set:
                downed_feeds.append(feed)
        return downed_feeds

    def process_feeds_metrics(self, feeds_to_check, table_name, time_string_choice):
        """
        Processes all hourly feeds in a particular dictionary format.
        :param feeds_to_check: feeds to be checked
        :param table_name: table to be queried
        :param time_string_choice: selection for time string to be used
        :return: list of feeds that are suspected to be down and list of feeds that submitted abnormal amounts
                 of domains
        """
        submitted_out_of_range_feeds = []
        for feed in feeds_to_check:
            check_time = self.select_dynamo_time_string(feeds_to_check, feed, time_string_choice)
            metric = self.get_feed_metrics(table_name, feed, check_time)
            if metric:
                feed_metrics = feeds_to_check.get(feed)
                metric_val = metric.get(feed_metrics.get('metric_name'))
                if metric_val:
                    if feed_metrics.get('min') > metric_val or \
                       feed_metrics.get('max') < metric_val:
                        submitted_out_of_range_feeds.append(feed + ", Amount Submitted: " + str(metric_val) +
                                                            ", Min Submission Amount " + str(feed_metrics.get('min')) +
                                                            ", Max Submission Amount : " + str(feed_metrics.get('max')))

        return submitted_out_of_range_feeds

    @staticmethod
    def get_dynamo_daily_time_string(hour):
        """
        Retrieves daily time string based off a user submitted hour
        :return: daily time string based off a user submitted hour
        """
        return (datetime.now(pytz.utc) - timedelta(days=1)).strftime("%Y-%m-%dT") + hour

    @staticmethod
    def get_dynamo_hourly_time_string():
        """
        Retrieves previous hour dynamo db time string.
        :return: previous hour dynamo db time string
        """
        return (datetime.now(pytz.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H").replace('/', '')

    @staticmethod
    def get_dynamo_weekly_time_string(hour, days_to_subtract):
        """
        Retrieves weekly time string based off a user submitted hour and day
        :return: weekly time string based off a user submitted hour and day
        """
        return (datetime.now(pytz.utc) - timedelta(days=days_to_subtract)).strftime("%Y-%m-%dT") + hour
