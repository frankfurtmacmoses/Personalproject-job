"""
Created on July 19, 2018

This script is designed to monitor Newly Observed Hostnames and
Newly Observed Domains feeds. This should run every hour and
confirm that the feeds have been running within the past hour.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""

# Python imports
from datetime import datetime, timedelta
from logging import getLogger
import pytz

# Cyberint imports
from cyberint_watchmen.universal_watchmen import Watchmen
from cyberint_aws.sns_alerts import raise_alarm

LOGGER = getLogger(__name__)

SUCCESS_MESSAGE = "NOH/D Feeds are up and running!"
ERROR = "ERROR: "
FAILURE_DOMAIN = ERROR + "The newly observed domain feed has gone down!"
FAILURE_HOSTNAME = ERROR + "The newly observed hostname feed has gone down!"
FAILURE_BOTH = ERROR + "Both newly observed hostname and domain feeds have gone down!"
FAILURE_SUBJECT = "Moloch watchmen detected an issue with NOH/D feed!"

BUCKET_NAME = "deteque-new-observable-data"
DOMAINS_PATH = "NewlyObservedDomains"
HOSTNAME_PATH = "NewlyObservedHostname"

SNS_TOPIC_ARN = "arn:aws:sns:us-east-1:405093580753:cyberintel-feeds-prod"

FILE_START = "ZMQ_Output_"
FILE_EXT = ".txt"


def check_for_existing_files(file_path, check_time):
    """
    Searches through file path and stops when it has found a file.
    NOTE: This process doesn't check that all 60 files exist, but that at least,
          1 exists. NOH/D feeds are up or stay down forever.
    :param file_path: the file path
    :param check_time: the time stamp for files to be checked
    :return: if any file was found
    """
    watcher = Watchmen(BUCKET_NAME)
    file_found = False
    count = 0
    # Goes through until it finds a file or all 60 files do not appear in S3.
    while not file_found and count != 60:
        key = file_path + check_time.strftime("%Y_%-m_%-d_%-H_%-m") + FILE_EXT
        file_found = watcher.validate_file_on_s3(key)
        check_time += timedelta(minutes=1)
        count += 1
    return file_found


def main():
    """
    main function
    :return: status of the NOH/D feed
    """
    status = SUCCESS_MESSAGE
    # Feeds are on both the same time
    check_time = datetime.now(pytz.utc) - timedelta(hours=1)
    # Hyphen before removes 0 in front of values. Eg 2018_07_06 becomes 2018_7_6
    parsed_date_time = check_time.strftime("%Y_%-m_%-d").split('_')
    file_path = '/' + parsed_date_time[0] + '/' + parsed_date_time[1] + '/' + parsed_date_time[2] + '/' + FILE_START
    domain_check = False
    hostname_check = False
    try:
        domain_check = check_for_existing_files(DOMAINS_PATH + file_path, check_time)
        hostname_check = check_for_existing_files(HOSTNAME_PATH + file_path, check_time)
    except Exception as ex:
        LOGGER.error(ex)

    if not domain_check or not hostname_check:
        if not domain_check and not hostname_check:
            status = FAILURE_BOTH
        elif not domain_check:
            status = FAILURE_DOMAIN
        elif not hostname_check:
            status = FAILURE_HOSTNAME
        raise_alarm(SNS_TOPIC_ARN, status, FAILURE_SUBJECT)

    LOGGER.info(status)
    return status
