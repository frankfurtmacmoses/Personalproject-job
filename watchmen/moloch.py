# Python imports
from datetime import datetime, timedelta
import pytz

# Watchmen imports
from watchmen.utils.universal_watchman import Watchmen


SUCCESS_MESSAGE = "NOH/D Feed is up and running!"
FAILURE_MESSAGE = "ERROR: NOH/D Feed has been down for an hour! No new data is coming through!"

BUCKET_NAME = "deteque-new-observable-data"
DOMAINS_PATH = "NewlyObservedDomains"
HOSTNAME_PATH = "NewlyObservedHostname"

FILE_START = "ZMQ_Output_"
FILE_EXT = ".txt"


def check_for_existing_files(file_path, check_time):
    watcher = Watchmen()
    file_found = False
    count = 0
    # Goes through until it finds a file or all 60 files do not appear in S3.
    while not file_found and count is not 60:
        key = file_path + check_time.strftime("%Y_%-m_%-d_%-H_%-m") + FILE_EXT
        file_found = watcher.validate_file_on_s3(BUCKET_NAME, key)
        check_time += timedelta(minutes=1)
        count += 1
    return file_found


def main():
    """
    main function
    :return: status of the NOH/D feed
    """
    status = SUCCESS_MESSAGE
    # Two different times since one feed is ahead of the other.
    # Other feed went down hard
    check_time_domain = datetime.now(pytz.utc) - timedelta(hours=1)
    # check_time_hostname = check_time_domain - timedelta(hours=3)
    # Hyphen before removes 0 in front of values.
    parsed_date_time = check_time_domain.strftime("%Y_%-m_%-d").split('_')
    file_path = '/' + parsed_date_time[0] + '/' + parsed_date_time[1] + '/' + parsed_date_time[2] + '/' + FILE_START
    domain_check = check_for_existing_files(DOMAINS_PATH + file_path, check_time_domain)
    # hostname_check = check_for_existing_files(HOSTNAME_PATH + file_path, check_time_hostname)
    if not domain_check:
        # or not hostname_check:
        status = FAILURE_MESSAGE
        # raise alarm
    print status
    return status


main()
