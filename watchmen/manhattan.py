"""
Created on July 30, 2018

This script is designed to monitor hourly feeds and ensure proper data flow.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
from logging import getLogger, basicConfig, INFO
# Cyberint imports
from watchmen.utils.universal_watchmen import Watchmen  # add to pypi :(
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


def bambenek_c2_ip(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Bambenek IP Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['IPV4_TIDE_SUCCESS'], 50, 300)


def cox_feed(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Cox Feed.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['IPV4_TIDE_SUCCESS'], 19000, 23000)


def Xylitol_CyberCrime(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Cybercrime Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI'], 30, 50)


def ecrimeX(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Ecrimex Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI_TIDE_SUCCESS'], 25, 75)


def G01Pack_DGA(watcher, metric):  # nopep8
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
    return watcher.check_feed_metric(metric['URI'], 5, 35)


def VX_Vault(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Vx Vault Scraper.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    # Allowed to submit zero URI's
    return watcher.check_feed_metric(metric['URI_TIDE_SUCCESS'], -1, 10)


def Zeus_Tracker(watcher, metric):  # nopep8
    """
    Ensures submitted domain range is valid for Zeus Tracker.
    :param watcher: universal watcher instantiation
    :param metric: metric of feed from dynamo db
    :return: checks for abnormalities in submission rate
    """
    return watcher.check_feed_metric(metric['URI_TIDE_SUCCESS'], 35, 55)


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of all hourly feeds
    """
    status = SUCCESS_MESSAGE
    feeds_to_check = {
        1: bambenek_c2_ip, 2: cox_feed, 3: Xylitol_CyberCrime, 4: ecrimeX, 5: G01Pack_DGA,
        6: tracker_h3x_eu, 7: VX_Vault, 8: Zeus_Tracker
    }
    watcher = Watchmen()
    downed_feeds = []
    submitted_out_of_range_feeds = []
    for count, feed in feeds_to_check.iteritems():
        feed_name = str(feed).split()[1]
        metric = watcher.get_feed_metrics(TABLE_NAME, feed_name)
        if metric:
            feed_func = feeds_to_check.get(count, lambda: NOT_A_FEED_ERROR)
            if not feed_func(watcher, metric):
                submitted_out_of_range_feeds.append(feed_name)
        else:
            downed_feeds.append(feed_name)

    if downed_feeds or submitted_out_of_range_feeds:
        status = FAILURE_MESSAGE
        message = (
                status + '\n' + ERROR_FEEDS + str(downed_feeds) + '\n' +
                ABNORMAL_SUBMISSIONS_MESSAGE + str(submitted_out_of_range_feeds)
        )
        print message
        # raise_alarm(SNS_TOPIC_ARN, message, SUBJECT_MESSAGE)
    LOGGER.info(status)
    return status
