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

ERROR_FEEDS = "FAILED/DOWNED FEEDS: "
ABNORMAL_SUBMISSIONS_MESSAGE = "ABNORMAL SUBMISSION AMOUNTS FROM THESE FEEDS: "

TABLE_NAME = "CyberInt-Reaper-prod-DynamoDbStack-3XBEIHSJPHBT-ReaperMetricsTable-1LHW3I46AEDQJ"
NOT_A_FEED_ERROR = "ERROR: Feed does not exist or is slotted in the wrong class!"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"


def bambenek_c2_ip(watcher, metric):
    """
    Ensures submitted domain range is valid for Bambenek IP Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['IPV4_TIDE_SUCCESS'], 50, 300)


def cox_feed(watcher, metric):
    """
    Ensures submitted domain range is valid for Cox Feed.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['IPV4_TIDE_SUCCESS'], 15000, 30000)


# pylint: disable=invalid-name
def Xylitol_CyberCrime(watcher, metric):
    """
    Ensures submitted domain range is valid for Cybercrime Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI'], 30, 50)


# pylint: disable=invalid-name
def ecrimeX(watcher, metric):
    """
    Ensures submitted domain range is valid for Ecrimex Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI_TIDE_SUCCESS'], 25, 400)


# pylint: disable=invalid-name
def G01Pack_DGA(watcher, metric):
    """
    Ensures submitted domain range is valid for G01 DGA.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['FQDN_TIDE_SUCCESS'], 15, 35)


def tracker_h3x_eu(watcher, metric):
    """
    Ensures submitted domain range is valid for Tracker H3x Eu.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI'], 5, 50)


# pylint: disable=invalid-name
def Zeus_Tracker(watcher, metric):
    """
    Ensures submitted domain range is valid for Zeus Tracker.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI_TIDE_SUCCESS'], 35, 55)


def process_feeds_metrics(feeds_to_check):
    """
    Processes all the feeds metrics
    :return: list of downed feeds and list of feeds that submitted abnormal amounts of domains
    """
    watcher = Watchmen()
    downed_feeds = []
    submitted_out_of_range_feeds = []
    for key, feed in feeds_to_check.iteritems():
        feed_name = str(feed).split()[1]
        metric = watcher.get_feed_metrics(TABLE_NAME, feed_name)
        if metric:
            feed_func = feeds_to_check.get(key, lambda: NOT_A_FEED_ERROR)
            if not feed_func(watcher, metric):
                submitted_out_of_range_feeds.append(feed_name)
        else:
            downed_feeds.append(feed_name)

    return downed_feeds, submitted_out_of_range_feeds


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    feeds_to_check = {
        1: bambenek_c2_ip, 2: cox_feed, 3: Xylitol_CyberCrime, 4: ecrimeX, 5: G01Pack_DGA,
        6: tracker_h3x_eu, 7: Zeus_Tracker
    }
    status = SUCCESS_MESSAGE
    try:
        downed_feeds, submitted_out_of_range_feeds = process_feeds_metrics(feeds_to_check)
        if downed_feeds or submitted_out_of_range_feeds:
            status = FAILURE_MESSAGE
            message = (
                    status + '\n' + ERROR_FEEDS + str(downed_feeds) + '\n' +
                    ABNORMAL_SUBMISSIONS_MESSAGE + str(submitted_out_of_range_feeds)
            )
            raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
    except Exception as ex:
        status = FAILURE_MESSAGE
        LOGGER.error(ex)

    LOGGER.info(status)
    return status
