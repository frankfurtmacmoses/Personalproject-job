"""
watchmen/models/moloch.py

Created on July 19, 2018

This script is designed to monitor Newly Observed Hostnames and
Newly Observed Domains feeds. This should run every hour and
confirm that the feeds have been running within the past hour.

@author: Daryan Hanshew
@email: dhanshew@infoblox.com

Refactored on July 11, 2019
@author: Jinchi Zhang
@email: jzhang@infoblox.com
"""

# Python imports
import traceback
import pytz
from datetime import datetime, timedelta

# Cyberint imports
from watchmen.utils.logger import get_logger
from watchmen.common.result import Result
from watchmen.config import settings
from watchmen.utils.s3 import validate_file_on_s3
from watchmen.common.watchman import Watchman

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

BUCKET_NAME = settings('moloch.bucket_name', "deteque-new-observable-data")
DOMAINS_PATH = settings('moloch.domain_name', "NewlyObservedDomains")
HOSTNAME_PATH = settings('moloch.hostname_path', "NewlyObservedHostname")

SNS_TOPIC_ARN = settings('moloch.sns_topic', "arn:aws:sns:us-east-1:405093580753:Watchmen_Test")

FILE_START = "ZMQ_Output_"
FILE_EXT = ".txt"

# Watchman profile
TARGET = "Newly Observed Data"


class Moloch(Watchman):
    """
    Class of Moloch
    """

    def __init__(self):
        pass

    def _check_for_existing_files(self, file_path, check_time):
        """
        Searches through file path and stops when it has found a file.
        NOTE: This process doesn't check that all 60 files exist, but that at least,
              1 exists. NOH/D feeds are up or stay down forever.
        @param file_path: <str> the file path
        @param check_time: <str> the time stamp for files to be checked
        @return: <bool> if any file was found
        """
        file_found = False
        count = 0
        # Goes through until it finds a file or all 60 files do not appear in S3.
        while not file_found and count != 60:
            key = file_path + check_time.strftime("%Y_%-m_%-d_%-H_%-m") + FILE_EXT
            file_found = validate_file_on_s3(BUCKET_NAME, key)
            check_time += timedelta(minutes=1)
            count += 1
        return file_found

    def _get_check_results(self):
        """
        checks if the domain and hostname contain existing files one hour ago
        @return: <bool>, <bool> the status of the domain and host name or None upon exception, None for exception
        """
        # Feeds are on both the same time
        check_time = datetime.now(pytz.utc) - timedelta(hours=1)
        # Hyphen before removes 0 in front of values. Eg 2018_07_06 becomes 2018_7_6
        parsed_date_time = check_time.strftime("%Y_%-m_%-d").split('_')
        file_path = '/' + parsed_date_time[0] + '/' + parsed_date_time[1] + '/' + parsed_date_time[2] + '/' + FILE_START

        try:
            domain_check = self._check_for_existing_files(DOMAINS_PATH + file_path, check_time)
            hostname_check = self._check_for_existing_files(HOSTNAME_PATH + file_path, check_time)
            return domain_check, hostname_check
        except Exception as ex:
            LOGGER.exception(traceback.extract_stack())
            LOGGER.info('*' * 80)
            LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
            return None, None

    def monitor(self) -> Result:
        pass
