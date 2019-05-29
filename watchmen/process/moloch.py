"""
Created on July 19, 2018

This script is designed to monitor Newly Observed Hostnames and
Newly Observed Domains feeds. This should run every hour and
confirm that the feeds have been running within the past hour.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

"""
# Python imports
import traceback
import pytz
from datetime import datetime, timedelta

# Cyberint imports
from watchmen.utils.universal_watchmen import Watchmen
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.logger import get_logger
from watchmen.config import settings

LOGGER = get_logger("Moloch", settings('logging.level', 'INFO'))

SUCCESS_MESSAGE = "NOH/D Feeds are up and running!"
ERROR = "ERROR: "
FAILURE_DOMAIN = ERROR + "The newly observed hostname feed has gone down! To view missing data go run the command " \
                           "aws s3 ls s3://deteque-new-observable-data/NewlyObservedDomains and head towards the " \
                           "most recent data. Afterwards contact Devops team to restart Domains tasks in AWS SaaS " \
                           "account."
FAILURE_HOSTNAME = ERROR + "The newly observed domains feed has gone down! To view missing data go run the command " \
                           "aws s3 ls s3://deteque-new-observable-data/NewlyObservedHostname and head towards the " \
                           "most recent data. Afterwards contact Devops team to restart Hostname tasks in AWS SaaS " \
                           "account."
FAILURE_BOTH = ERROR + "Both hostname and domains feed have gone down! To view missing data go run the command " \
                           "aws s3 ls s3://deteque-new-observable-data/NewlyObservedHostname and " \
                           "run the command s3 ls s3://deteque-new-observable-data/NewlyObservedDomains  " \
                           "head towards the most recent data. Afterwards contact Devops team to restart Hostname " \
                           "and Domains tasks in AWS SaaS account."

FAILURE_SUBJECT = "Moloch watchmen detected an issue with NOH/D feed!"

EXCEPTION_SUBJECT = "Moloch watchmen reached an exception!"
EXCEPTION_MESSAGE = "The newly observed domain feeds and hostname feeds reached an exception during the file checking" \
                    " process due to the following:\n\n{}\n\nPlease look at the logs for more insight."

BUCKET_NAME = "deteque-new-observable-data"
DOMAINS_PATH = "NewlyObservedDomains"
HOSTNAME_PATH = "NewlyObservedHostname"

SNS_TOPIC_ARN = settings('moloch.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

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


def get_check_results():
    """
    checks if the domain and hostname contain existing files one hour ago
    @return: the status of the domain and host name or None upon exception
    """
    # Feeds are on both the same time
    check_time = datetime.now(pytz.utc) - timedelta(hours=1)
    # Hyphen before removes 0 in front of values. Eg 2018_07_06 becomes 2018_7_6
    parsed_date_time = check_time.strftime("%Y_%-m_%-d").split('_')
    file_path = '/' + parsed_date_time[0] + '/' + parsed_date_time[1] + '/' + parsed_date_time[2] + '/' + FILE_START

    try:
        domain_check = check_for_existing_files(DOMAINS_PATH + file_path, check_time)
        hostname_check = check_for_existing_files(HOSTNAME_PATH + file_path, check_time)
        return domain_check, hostname_check
    except Exception as ex:
        LOGGER.error(ex)
        trace = traceback.format_exc(ex)
        raise_alarm(SNS_TOPIC_ARN, EXCEPTION_MESSAGE.format(trace), EXCEPTION_SUBJECT)
        return None, None


# pylint: disable=unused-argument
def main(event, context):
    """
    Confirms that the NOH/D feeds have been running within the past hour
    :return: status of the NOH/D feeds
    """
    domain_check, host_check = get_check_results()
    status = notify(domain_check, host_check)

    LOGGER.info(status)
    return status


def notify(domain_check, hostname_check):
    """
    Sends an email notification upon failure; otherwise, just returns status
    @param domain_check: whether or not files exist on the domain
    @param hostname_check: whether or not files exist on the hostname
    @return: the status of the check
    """
    status = SUCCESS_MESSAGE
    if domain_check is None or hostname_check is None:
        return EXCEPTION_SUBJECT

    if not domain_check or not hostname_check:
        if not domain_check and not hostname_check:
            status = FAILURE_BOTH
        elif not domain_check:
            status = FAILURE_DOMAIN
        elif not hostname_check:
            status = FAILURE_HOSTNAME
        raise_alarm(SNS_TOPIC_ARN, status, FAILURE_SUBJECT)
    return status
