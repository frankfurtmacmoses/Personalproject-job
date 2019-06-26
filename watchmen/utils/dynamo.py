"""
Created on July 17, 2018

Module containing functions for AWS ECS

@author Daryan Hanshew
@email dhanshew@infoblox.com

Refactored on May 28, 2019
@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import pytz
from datetime import datetime, timedelta
from logging import getLogger

LOGGER = getLogger(__name__)


def select_dynamo_time_string(feeds_to_check, feed, time_string_choice):
    """
    Selects the time string to use based off choice.
    :param feeds_to_check: feeds currently being looked at
    :param feed: the feed itself being checked
    :param time_string_choice: the selection for time string by user
            0 = hourly, 1 = daily, 2 = weekly
    :return: time string for dynamo db
    """
    time_string = None
    feed_item = feeds_to_check.get(feed)
    time_string_chart = {
        0: get_dynamo_hourly_time_string,
        1: get_dynamo_daily_time_string,
        2: get_dynamo_weekly_time_string,
    }
    if time_string_choice in time_string_chart:
        time_string = time_string_chart.get(time_string_choice)(feed_item)
    return time_string


def get_dynamo_daily_time_string(feed):
    """
    Retrieves daily time string based off a user submitted hour
    :return: daily time string based off a user submitted hour
    """
    hour = feed.get('hour_submitted')
    return (datetime.now(pytz.utc) - timedelta(days=1)).strftime("%Y-%m-%dT") + hour


def get_dynamo_hourly_time_string(feed):
    """
    Retrieves previous hour dynamo db time string.
    :return: previous hour dynamo db time string
    """
    return (datetime.now(pytz.utc) - timedelta(hours=1)).strftime("%Y-%m-%dT%H").replace('/', '')


def get_dynamo_weekly_time_string(feed):
    """
    Retrieves weekly time string based off a user submitted hour and day
    :return: weekly time string based off a user submitted hour and day
    """
    days_to_subtract, hour = feed.get('days_to_subtract'), feed.get('hour_submitted')
    return (datetime.now(pytz.utc) - timedelta(days=days_to_subtract)).strftime("%Y-%m-%dT") + hour
