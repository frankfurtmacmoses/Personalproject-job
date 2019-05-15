"""
Created on July 17, 2018

This module is meant to be used as a helper for other
Watchmen scripts. Most of this class can be utilized
for verifying simple checks in S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

Refactored on May 28, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import boto3
import pytz
from boto3.dynamodb.conditions import Key
from datetime import datetime
from logging import getLogger
from watchmen.utils.dynamo import select_dynamo_time_string


EMPTY_METRIC_ERROR = "No metric found for: "
LOGGER = getLogger(__name__)


def get_feed_metrics(table_name, feed, check_time):
    """
    Retrieves metrics for a particular feed.
    :param table_name: name of table being searched
    :param feed: feed itself being checked
    :param check_time: time being checked in metrics table
    :return: metrics for a particular feed
    """
    metric = {}
    dynamo_client = boto3.resource('dynamodb')

    table = dynamo_client.Table(table_name)
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


def process_feeds_logs(feed_names, start, end, log_group_name=""):
    """
    Processes all the logs for feeds and ensures that a log was created.
    :param feed_names: names of all feeds to be processed
    :param start: start time of processing logs
    :param end: end time of processing logs
    :param log_group_name: name of the log group to process
    :return: a list if any feeds that are suspected to be down
    """
    log_client = boto3.client('logs')
    response = None
    feed_name_set = set()
    downed_feeds = []

    while start < end:
        if not response:
            response = log_client.describe_log_streams(
                logGroupName=log_group_name,
                orderBy='LastEventTime',
                descending=True,
                limit=50
            )
        else:
            response = log_client.describe_log_streams(
                logGroupName=log_group_name,
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


def process_feeds_metrics(feeds_to_check, table_name, time_string_choice):
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
        check_time = select_dynamo_time_string(feeds_to_check, feed, time_string_choice)
        metric = get_feed_metrics(table_name, feed, check_time)
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
